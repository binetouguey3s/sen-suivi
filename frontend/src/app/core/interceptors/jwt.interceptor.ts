import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';

import { AuthService } from '../services/auth.service';

export const jwtInterceptor: HttpInterceptorFn = (requete, suite) => {
  const jeton = inject(AuthService).jetonAcces();
  if (!jeton) return suite(requete);
  return suite(requete.clone({ setHeaders: { Authorization: `Bearer ${jeton}` } }));
};
