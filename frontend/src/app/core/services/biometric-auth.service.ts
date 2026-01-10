import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, from, throwError } from 'rxjs';
import { switchMap, catchError } from 'rxjs/operators';
import { environment } from '../../environments/environment';

export interface BiometricDevice {
  id: number;
  device_type: 'fingerprint' | 'face_id';
  device_id: string;
  device_name: string;
  credential_id: string;
  is_active: boolean;
  registered_at: string;
  last_used: string | null;
}

@Injectable({
  providedIn: 'root'
})
export class BiometricAuthService {
  private apiUrl = `${environment.apiUrl}`

  constructor(private http: HttpClient) {}

  /* -------------------- Availability -------------------- */

  isBiometricAvailable(): boolean {
    return !!window.PublicKeyCredential;
  }

  async detectAvailableBiometrics(): Promise<{ fingerprint: boolean; faceId: boolean }> {
    if (!this.isBiometricAvailable()) {
      return { fingerprint: false, faceId: false };
    }

    const available =
      await PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable();

    const ua = navigator.userAgent.toLowerCase();
    const isIOS = /iphone|ipad/.test(ua);
    const isAndroid = /android/.test(ua);

    return {
      faceId: available && isIOS,
      fingerprint: available && (isAndroid || !isIOS)
    };
  }

  /* -------------------- Registration -------------------- */

  registerBiometric(
    deviceType: 'fingerprint' | 'face_id',
    deviceName: string
  ): Observable<BiometricDevice> {
    return this.http.get<any>(`${this.apiUrl}/users/me/`).pipe(
      switchMap(user =>
        from(this.createCredential(user)).pipe(
          switchMap(cred =>
            this.http.post<BiometricDevice>(
              `${this.apiUrl}/users/register_biometric/`,
              {
                device_type: deviceType,
                device_id: cred.deviceId,
                device_name: deviceName,
                public_key: cred.publicKey,
                verification_token: cred.attestation
              }
            )
          )
        )
      ),
      catchError(err => {
        console.error(err);
        return throwError(() => new Error('Biometric registration failed'));
      })
    );
  }

  private async createCredential(user: any): Promise<{
    deviceId: string;
    publicKey: string;
    attestation: string;
  }> {
    const challenge = crypto.getRandomValues(new Uint8Array(32)).buffer;

    const options: PublicKeyCredentialCreationOptions = {
      challenge,
      rp: {
        name: 'Advance Company',
        id: window.location.hostname
      },
      user: {
        id: new TextEncoder().encode(user.id.toString()),
        name: user.email,
        displayName: user.full_name
      },
      pubKeyCredParams: [
        { type: 'public-key', alg: -7 },
        { type: 'public-key', alg: -257 }
      ],
      authenticatorSelection: {
        authenticatorAttachment: 'platform',
        userVerification: 'required'
      },
      timeout: 60000
    };

    const credential = (await navigator.credentials.create({
      publicKey: options
    })) as PublicKeyCredential;

    if (!credential) {
      throw new Error('Credential creation failed');
    }

    const response = credential.response as AuthenticatorAttestationResponse;

    return {
      deviceId: this.bufferToBase64(credential.rawId),
      publicKey: this.bufferToBase64(response.attestationObject),
      attestation: this.bufferToBase64(response.clientDataJSON)
    };
  }

  /* -------------------- Login -------------------- */

  biometricLogin(email: string, deviceId: string): Observable<any> {
    return this.http
      .post<any>(`${this.apiUrl}/users/biometric_challenge/`, {
        email,
        device_id: deviceId
      })
      .pipe(
        switchMap(res =>
          from(this.signChallenge(res.challenge, res.credential_id)).pipe(
            switchMap(sig =>
              this.http.post(`${this.apiUrl}/users/biometric_login/`, {
                email,
                credential_id: res.credential_id,
                signature: sig.signature,
                authenticator_data: sig.authenticatorData,
                client_data: sig.clientData
              })
            )
          )
        ),
        catchError(err => {
          console.error(err);
          return throwError(() => new Error('Biometric login failed'));
        })
      );
  }

  private async signChallenge(
    challenge: string,
    credentialId: string
  ): Promise<{
    signature: string;
    authenticatorData: string;
    clientData: string;
  }> {
    const options: PublicKeyCredentialRequestOptions = {
      challenge: this.base64ToBuffer(challenge),
      allowCredentials: [
        {
          id: this.base64ToBuffer(credentialId),
          type: 'public-key',
          transports: ['internal']
        }
      ],
      userVerification: 'required',
      timeout: 60000
    };

    const assertion = (await navigator.credentials.get({
      publicKey: options
    })) as PublicKeyCredential;

    const response = assertion.response as AuthenticatorAssertionResponse;

    return {
      signature: this.bufferToBase64(response.signature),
      authenticatorData: this.bufferToBase64(response.authenticatorData),
      clientData: this.bufferToBase64(response.clientDataJSON)
    };
  }

  /* -------------------- Devices -------------------- */

  getBiometricDevices(): Observable<BiometricDevice[]> {
    return this.http.get<BiometricDevice[]>(`${this.apiUrl}/users/biometric_devices/`);
  }

  removeBiometricDevice(deviceId: string): Observable<any> {
    return this.http.delete(`${this.apiUrl}/users/remove_biometric/`, {
      body: { device_id: deviceId }
    });
  }

  /* -------------------- Utils -------------------- */

  private bufferToBase64(buffer: ArrayBuffer): string {
    return btoa(String.fromCharCode(...new Uint8Array(buffer)));
  }

  private base64ToBuffer(base64: string): ArrayBuffer {
    const binary = atob(base64);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) {
      bytes[i] = binary.charCodeAt(i);
    }
    return bytes.buffer;
  }
}
