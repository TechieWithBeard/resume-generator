import {
  Directive,
  ElementRef,
  Input,
  OnChanges,
  OnDestroy,
  SimpleChanges,
  inject,
  AfterViewInit,
} from '@angular/core';

@Directive({
  selector: 'iframe[appIframeHtml]',
  standalone: true,
})
export class IframeHtmlDirective implements OnChanges, AfterViewInit, OnDestroy {
  @Input('appIframeHtml') html = '';
  @Input() autoHeight = true;
  @Input() extraHeight = 24;

  private readonly el = inject(ElementRef<HTMLIFrameElement>);
  private resizeObserver: ResizeObserver | null = null;
  private heightTimer1: ReturnType<typeof setTimeout> | null = null;
  private heightTimer2: ReturnType<typeof setTimeout> | null = null;

  ngAfterViewInit(): void {
    this.render();
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['html']) {
      this.render();
    }
  }

  ngOnDestroy(): void {
    this.cleanup();
  }

  private cleanup(): void {
    if (this.resizeObserver) {
      this.resizeObserver.disconnect();
      this.resizeObserver = null;
    }
    if (this.heightTimer1) {
      clearTimeout(this.heightTimer1);
      this.heightTimer1 = null;
    }
    if (this.heightTimer2) {
      clearTimeout(this.heightTimer2);
      this.heightTimer2 = null;
    }
  }

  private render(): void {
    const iframe = this.el.nativeElement;
    if (!iframe) return;

    this.cleanup();

    const content = this.html || '';
    if (!content) {
      try {
        const doc = iframe.contentWindow?.document || iframe.contentDocument;
        if (doc) {
          doc.open();
          doc.write('');
          doc.close();
        }
      } catch {}
      return;
    }

    try {
      const doc = iframe.contentWindow?.document || iframe.contentDocument;
      if (doc) {
        doc.open();
        doc.write(content);
        doc.close();

        if (this.autoHeight) {
          this.setupAutoHeight(doc);
        }
        return;
      }
    } catch (err) {
      console.warn('Direct iframe document write failed, falling back to srcdoc:', err);
    }

    // Fallback if direct contentDocument is not accessible
    iframe.srcdoc = content;
    if (this.autoHeight) {
      setTimeout(() => this.adjustHeight(), 100);
    }
  }

  private setupAutoHeight(doc: Document): void {
    // Initial immediate calculation
    this.adjustHeight();

    // Recalculate when web fonts (Google Fonts: Inter, Merriweather, JetBrains Mono, etc.) load
    try {
      if (doc.fonts && typeof doc.fonts.ready?.then === 'function') {
        doc.fonts.ready.then(() => {
          this.adjustHeight();
        });
      }
    } catch {}

    // Timers for layout settling and image/font rendering
    this.heightTimer1 = setTimeout(() => this.adjustHeight(), 60);
    this.heightTimer2 = setTimeout(() => this.adjustHeight(), 250);

    // Dynamic resize observer for internal content adjustments
    if (typeof ResizeObserver !== 'undefined' && doc.body) {
      try {
        this.resizeObserver = new ResizeObserver(() => {
          this.adjustHeight();
        });
        this.resizeObserver.observe(doc.body);
      } catch {}
    }
  }

  private adjustHeight(): void {
    const iframe = this.el.nativeElement;
    if (!iframe) return;

    try {
      const doc = iframe.contentDocument || iframe.contentWindow?.document;
      if (doc && doc.body) {
        doc.body.style.overflow = 'hidden';
        const h = Math.max(doc.body.scrollHeight, doc.documentElement.scrollHeight);
        if (h > 0) {
          const target = `${h + this.extraHeight}px`;
          if (iframe.style.height !== target) {
            iframe.style.height = target;
          }
        }
      }
    } catch {}
  }
}
