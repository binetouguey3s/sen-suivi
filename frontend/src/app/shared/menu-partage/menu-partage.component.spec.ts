import { Component } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { MenuPartageComponent } from './menu-partage.component';

const TITRE = 'Quand tout s’accumule : organiser sa semaine';
const URL_PROPRE = 'https://sensuivi.sn/ressources/12';

// Deux boutons, un seul menu : comme sur la page d'une ressource
@Component({
  standalone: true,
  imports: [MenuPartageComponent],
  template: `
    <button #haut id="haut" aria-haspopup="menu" [attr.aria-expanded]="menu.ouvertPour(haut)" (click)="menu.basculer(haut)">
      Partager
    </button>
    <button #bas id="bas" (click)="menu.basculer(bas)">Partager</button>
    <p id="ailleurs">Ailleurs</p>
    <ss-menu-partage #menu [titre]="titre" [url]="url" />
  `,
})
class HoteComponent {
  titre = TITRE;
  url = URL_PROPRE;
}

describe('MenuPartageComponent', () => {
  let fixture: ComponentFixture<HoteComponent>;
  let hote: HTMLElement;

  const menu = (): HTMLElement | null => hote.querySelector('[role="menu"]');
  const item = (texte: string): HTMLElement =>
    [...hote.querySelectorAll<HTMLElement>('[role="menuitem"]')].find((e) => e.textContent!.includes(texte))!;
  const bouton = (id: string): HTMLButtonElement => hote.querySelector(`#${id}`)!;

  async function stabiliser(): Promise<void> {
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
  }

  async function ouvrir(id = 'haut'): Promise<void> {
    bouton(id).click();
    await stabiliser();
  }

  beforeEach(async () => {
    await TestBed.configureTestingModule({ imports: [HoteComponent] }).compileComponents();
    fixture = TestBed.createComponent(HoteComponent);
    hote = fixture.nativeElement;
    document.body.appendChild(hote);
    await stabiliser();
  });

  afterEach(() => {
    hote.remove();
    vi.restoreAllMocks();
  });

  it('s’ouvre sous le bouton avec ses quatre actions, et met le focus sur la première', async () => {
    await ouvrir();

    expect(menu()).not.toBeNull();
    expect(bouton('haut').getAttribute('aria-expanded')).toBe('true');
    const libelles = [...hote.querySelectorAll('[role="menuitem"]')].map((e) => e.textContent!.trim());
    expect(libelles).toEqual(['Copier le lien', 'WhatsApp', 'E-mail', 'Enregistrer en PDF']);
    expect(document.activeElement).toBe(item('Copier le lien'));
  });

  it('les deux boutons ouvrent le même menu', async () => {
    await ouvrir('bas');
    expect(menu()).not.toBeNull();
    expect(bouton('haut').getAttribute('aria-expanded')).toBe('false');
  });

  it('les flèches parcourent les choix', async () => {
    await ouvrir();
    menu()!.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowDown', bubbles: true }));
    expect(document.activeElement).toBe(item('WhatsApp'));
    menu()!.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowUp', bubbles: true }));
    menu()!.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowUp', bubbles: true }));
    expect(document.activeElement).toBe(item('Enregistrer en PDF'));
  });

  it('Échap ferme le menu et rend le focus au bouton', async () => {
    await ouvrir();
    menu()!.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
    await stabiliser();

    expect(menu()).toBeNull();
    expect(document.activeElement).toBe(bouton('haut'));
  });

  it('un clic à l’extérieur ferme le menu', async () => {
    await ouvrir();
    hote.querySelector<HTMLElement>('#ailleurs')!.click();
    await stabiliser();

    expect(menu()).toBeNull();
  });

  it('« Copier le lien » copie l’adresse propre et l’annonce', async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, 'clipboard', { value: { writeText }, configurable: true });

    await ouvrir();
    item('Copier le lien').click();
    await stabiliser();

    expect(writeText).toHaveBeenCalledWith(URL_PROPRE);
    expect(hote.querySelector('[role="status"]')!.textContent).toContain('Lien copié');
    expect(menu()).toBeNull();
  });

  it('le lien WhatsApp et l’e-mail sont encodés', async () => {
    await ouvrir();

    const whatsapp = item('WhatsApp') as HTMLAnchorElement;
    expect(whatsapp.getAttribute('href')).toBe(
      `https://wa.me/?text=${encodeURIComponent(`${TITRE} — une ressource bien-être Sen Suivi : ${URL_PROPRE}`)}`,
    );
    expect(whatsapp.target).toBe('_blank');
    expect(whatsapp.rel).toContain('noopener');

    const courriel = item('E-mail').getAttribute('href')!;
    expect(courriel.startsWith(`mailto:?subject=${encodeURIComponent(TITRE)}&body=`)).toBe(true);
    const corps = decodeURIComponent(courriel.split('&body=')[1]);
    expect(corps).toContain(`« ${TITRE} »`);
    expect(corps).toContain(URL_PROPRE);
  });

  it('« Enregistrer en PDF » imprime avec le titre de la ressource, puis le restaure', async () => {
    document.title = 'Sen Suivi';
    let titrePendantImpression = '';
    const imprimer = vi.spyOn(window, 'print').mockImplementation(() => {
      titrePendantImpression = document.title;
    });

    await ouvrir();
    item('Enregistrer en PDF').click();

    expect(imprimer).toHaveBeenCalledTimes(1);
    expect(titrePendantImpression).toBe(`${TITRE} — Sen Suivi`);
    window.dispatchEvent(new Event('afterprint'));
    expect(document.title).toBe('Sen Suivi');
  });
});
