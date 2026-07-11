import { HttpInterceptorFn } from '@angular/common/http';
import { tap } from 'rxjs/operators';
import { environment } from '../../environments/environment';

export const timingInterceptor: HttpInterceptorFn = (req, next) => {
  if (environment.production) return next(req);

  const started = performance.now();
  const method = req.method;
  const url = req.url.replace(/^.*\/api\/v1/, '/api/v1');

  return next(req).pipe(
    tap({
      next: () => {
        const elapsed = (performance.now() - started).toFixed(0);
        const color = +elapsed < 300 ? 'color:#22c55e' : +elapsed < 1000 ? 'color:#f59e0b' : 'color:#ef4444';
        console.log(`%c⏱ ${method} ${url} — ${elapsed}ms`, color);
      },
      error: (err) => {
        const elapsed = (performance.now() - started).toFixed(0);
        console.warn(`⏱ ${method} ${url} — ${elapsed}ms [${err.status}]`);
      },
    })
  );
};
