import { Component, EventEmitter, HostListener, Input, Output } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-modal',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './modal.component.html',
  styleUrl: './modal.component.scss',
  host: {
    '[class.open]': 'isOpen',
    '[style.display]': 'isOpen ? "block" : "none"',
  },
})
export class ModalComponent {
  @Input() isOpen: boolean = false;
  @Input() title: string = '';
  @Input() maxWidth: string = 'max-w-3xl';
  @Output() close = new EventEmitter<void>();

  @HostListener('document:keydown.escape')
  onEscape() {
    if (this.isOpen) {
      this.close.emit();
    }
  }

  onBackdropClick() {
    this.close.emit();
  }
}
