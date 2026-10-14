import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { describe, expect, it, vi } from 'vitest';

import { API_BASE_URL } from '../../core/config/api.config';
import { SuiviHumeurService } from '../../core/services/suivi-humeur.service';
import { JournalComponent } from './journal.component';
import { phrasesDuJour } from './phrases';

async function afficher() {
  const publier = vi.fn().mockResolvedValue({});
  await TestBed.configureTestingModule({
    imports: [JournalComponent],
    providers: [provideRouter([]), provideHttpClient(), provideHttpClientTesting(), { provide: SuiviHumeurService, useValue: { publier } }],
  }).compileComponents();
  const fixture = TestBed.createComponent(JournalComponent);
  fixture.detectChanges();
  const http = TestBed.inject(HttpTestingController);
  http.expectOne(`${API_BASE_URL}/suivi-humeur?periode=30j`).flush([]);
  await fixture.whenStable();
  fixture.detectChanges();
  return { fixture, hote: fixture.nativeElement as HTMLElement, publier, http };
}

describe('JournalComponent, phrases pour commencer', () => {
  it('affiche les trois phrases du jour sous la note', async () => {
    const { hote } = await afficher();
    const puces = [...hote.querySelectorAll('.journal__phrase')].map((b) => b.textContent!.trim());
    expect(puces).toEqual(phrasesDuJour(new Date()));
  });

  it('un clic insère le début de phrase dans la note', async () => {
    const { fixture, hote } = await afficher();
    const puce = hote.querySelector<HTMLButtonElement>('.journal__phrase')!;
    puce.click();
    fixture.detectChanges();

    const note = hote.querySelector<HTMLTextAreaElement>('#journal-note')!;
    expect(note.value).toBe(`${puce.textContent!.trim().replace(/…$/, '')} `);
    expect(document.activeElement === note || !document.body.contains(note)).toBe(true);
    expect(hote.querySelector('.journal__compteur')!.textContent).toContain('/ 1000');
  });

  it('la note accepte 1 000 caractères', async () => {
    const { hote } = await afficher();
    expect(hote.querySelector('#journal-note')!.getAttribute('maxlength')).toBe('1000');
  });

  it('la note n’est envoyée qu’au journal, jamais à Titou', async () => {
    const { fixture, hote, publier, http } = await afficher();
    hote.querySelector<HTMLButtonElement>('.journal__phrase')!.click();
    fixture.detectChanges();
    hote.querySelector<HTMLButtonElement>('ss-mood-selector button')!.click();
    fixture.detectChanges();
    [...hote.querySelectorAll<HTMLButtonElement>('button')].find((b) => /Enregistrer/.test(b.textContent!))!.click();
    await new Promise((r) => setTimeout(r));
    fixture.detectChanges();
    // Seul appel réseau après l'enregistrement : le journal qui se recharge
    http.match(`${API_BASE_URL}/suivi-humeur?periode=30j`).forEach((r) => r.flush([]));

    expect(publier).toHaveBeenCalledTimes(1);
    expect(publier.mock.calls[0][1].note).toMatch(/ $/);
    http.verify();
  });
});
