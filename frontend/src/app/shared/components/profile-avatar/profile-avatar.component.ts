import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-profile-avatar',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './profile-avatar.component.html',
    styleUrls: ['./profile-avatar.component.scss']
})
export class ProfileAvatarComponent {
  @Input() photoUrl: string | null = null;
  @Input() fullName: string = '';
  @Input() size: 'xs' | 'sm' | 'md' | 'lg' | 'xl' = 'md';
  
  get containerClass(): string {
    const sizes = {
      xs: 'w-6 h-6 text-xs',
      sm: 'w-8 h-8 text-sm',
      md: 'w-10 h-10 text-base',
      lg: 'w-16 h-16 text-2xl',
      xl: 'w-20 h-20 text-3xl'
    };
    
    return `${sizes[this.size]} bg-gradient-to-br from-blue-600 to-indigo-700 rounded-full flex items-center justify-center text-white font-bold overflow-hidden`;
  }
  
  get textClass(): string {
    return 'select-none';
  }
  
  get initials(): string {
    if (!this.fullName) return '';
    
    const parts = this.fullName.trim().split(' ');
    if (parts.length >= 2) {
      return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
    }
    return this.fullName.charAt(0).toUpperCase();
  }
  
  onImageError(): void {
    this.photoUrl = null;
  }
}
