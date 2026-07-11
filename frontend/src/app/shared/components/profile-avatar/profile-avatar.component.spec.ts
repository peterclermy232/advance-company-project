import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ProfileAvatarComponent } from './profile-avatar.component';

describe('ProfileAvatarComponent', () => {
  let fixture: ComponentFixture<ProfileAvatarComponent>;
  let component: ProfileAvatarComponent;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ProfileAvatarComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(ProfileAvatarComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should default size to "md"', () => {
    expect(component.size).toBe('md');
  });

  it('should default photoUrl to null', () => {
    expect(component.photoUrl).toBeNull();
  });

  it('should return initials for two-word name', () => {
    component.fullName = 'John Doe';
    expect(component.initials).toBe('JD');
  });

  it('should return first and last initials for multi-word name', () => {
    component.fullName = 'John Michael Doe';
    expect(component.initials).toBe('JD');
  });

  it('should return single initial for one-word name', () => {
    component.fullName = 'Alice';
    expect(component.initials).toBe('A');
  });

  it('should return empty string when fullName is empty', () => {
    component.fullName = '';
    expect(component.initials).toBe('');
  });

  it('should set photoUrl to null on image error', () => {
    component.photoUrl = 'https://example.com/photo.jpg';
    component.onImageError();
    expect(component.photoUrl).toBeNull();
  });

  it('containerClass should include size-specific class for xs', () => {
    component.size = 'xs';
    expect(component.containerClass).toContain('w-6 h-6');
  });

  it('containerClass should include size-specific class for lg', () => {
    component.size = 'lg';
    expect(component.containerClass).toContain('w-16 h-16');
  });
});
