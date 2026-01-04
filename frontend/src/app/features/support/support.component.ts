import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { HeaderComponent } from '../../shared/components/header/header.component';
import { SidebarComponent } from '../../shared/components/sidebar/sidebar.component';
import { NotificationService } from '../../core/services/notification.service';

@Component({
  selector: 'app-support',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, HeaderComponent, SidebarComponent],
  templateUrl: './support.component.html',
  styleUrls: ['./support.component.scss']
})
export class SupportComponent {
  private fb = inject(FormBuilder);
  private notificationService = inject(NotificationService);

  sidebarOpen = true;
  isSubmitting = false;
  contactForm: FormGroup;

  faqs = [
    {
      question: 'How do I make a deposit?',
      answer: 'Navigate to the Financial section and choose your preferred payment method (M-Pesa, Bank Transfer, or Mansa-X). Fill in the required details and submit.'
    },
    {
      question: 'How do I add a beneficiary?',
      answer: 'Go to Beneficiary Management and click the "Add Beneficiary" button. Fill in all required information and upload necessary documents.'
    },
    {
      question: 'How do I upload documents?',
      answer: 'Visit the Document Centre, click "Upload Document", select the category, choose your file, and submit.'
    },
    {
      question: 'How can I view my financial reports?',
      answer: 'Navigate to the Reports section where you can generate and download various financial reports.'
    },
    {
      question: 'What should I do if I forgot my password?',
      answer: 'Click on "Forgot Password" on the login page and follow the instructions sent to your email.'
    }
  ];

  constructor() {
    this.contactForm = this.fb.group({
      subject: ['', Validators.required],
      message: ['', [Validators.required, Validators.minLength(10)]]
    });
  }

  toggleSidebar() {
    this.sidebarOpen = !this.sidebarOpen;
  }

  onSubmitContact() {
    if (this.contactForm.valid) {
      this.isSubmitting = true;
      
      // Simulate API call
      setTimeout(() => {
        this.notificationService.success('Message sent successfully. We will get back to you soon.');
        this.contactForm.reset();
        this.isSubmitting = false;
      }, 1500);
    }
  }
}