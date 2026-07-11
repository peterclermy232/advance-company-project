import { ComponentFixture, TestBed } from '@angular/core/testing';
import { StatCardComponent } from './stat-card.component';

describe('StatCardComponent', () => {
  let fixture: ComponentFixture<StatCardComponent>;
  let component: StatCardComponent;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [StatCardComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(StatCardComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should default color to "blue"', () => {
    expect(component.color).toBe('blue');
  });

  it('should default label to empty string', () => {
    expect(component.label).toBe('');
  });

  it('should default value to empty string', () => {
    expect(component.value).toBe('');
  });

  it('should accept label input', () => {
    component.label = 'Total Members';
    fixture.detectChanges();
    expect(component.label).toBe('Total Members');
  });

  it('should accept value input', () => {
    component.value = '42';
    fixture.detectChanges();
    expect(component.value).toBe('42');
  });

  it('should accept optional trend input', () => {
    component.trend = '+5%';
    fixture.detectChanges();
    expect(component.trend).toBe('+5%');
  });

  it('should accept color input', () => {
    component.color = 'green';
    fixture.detectChanges();
    expect(component.color).toBe('green');
  });
});
