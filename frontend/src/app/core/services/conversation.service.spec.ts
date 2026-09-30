import { signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { ReponseChatbot } from '../models/chatbot';
import { AuthService } from './auth.service';
import { ChatbotService } from './chatbot.service';
import { ConversationService } from './conversation.service';
import { UrgenceService } from './urgence.service';

const REPONSE: ReponseChatbot = {
  conversation_id: 42,
  reponse: 'Je vous écoute.',
  source_reponse: 'REGLE',
  urgence: false,
  intention: null,
  ressource: null,
};

describe('ConversationService', () => {
  const identifiant = signal<number | null>(null);
  const typeCompte = signal<string | null>(null);
  const envoyer = vi.fn<ChatbotService['envoyer']>();
  const creer = vi.fn<ChatbotService['creer']>();
  const lister = vi.fn<ChatbotService['lister']>();
  const lire = vi.fn<ChatbotService['lire']>();
  const supprimer = vi.fn<ChatbotService['supprimer']>();
  let service: ConversationService;

  beforeEach(() => {
    identifiant.set(null);
    typeCompte.set(null);
    [envoyer, creer, lister, lire, supprimer].forEach((f) => f.mockReset());
    sessionStorage.clear();
    TestBed.resetTestingModule();
    TestBed.configureTestingModule({
      providers: [
        { provide: AuthService, useValue: { identifiant, typeCompte } },
        { provide: ChatbotService, useValue: { envoyer, creer, lister, lire, supprimer } },
      ],
    });
    service = TestBed.inject(ConversationService);
    TestBed.tick();
  });

  it('garde le jeton d’urgence remis quand une détresse est détectée', async () => {
    envoyer.mockResolvedValue({ ...REPONSE, urgence: true, jeton_urgence: 'jeton-signe' });

    await service.envoyer('Je n’en peux plus');

    expect(TestBed.inject(UrgenceService).enDetresse()).toBe(true);
    expect(TestBed.inject(UrgenceService).jeton()).toBe('jeton-signe');
  });

  it('affiche le professionnel suggéré par l’algorithme sous la réponse de Titou', async () => {
    const pro = { id: 3, nom: 'Moussa Ba', specialite_affichee: 'Sophrologue', ville: 'Mbour', raison: 'Sophrologue, Moussa Ba accompagne le stress.' };
    envoyer.mockResolvedValue({ ...REPONSE, orientation_professionnel: true, professionnel_suggere: pro });

    await service.envoyer('Je veux un spécialiste');

    const derniere = service.messages().at(-1)!;
    expect(derniere.professionnel).toEqual(pro);
    expect(derniere.orientationAnnuaire).toBe(false);
  });

  it('sans suggestion personnalisée, propose simplement l’annuaire', async () => {
    envoyer.mockResolvedValue({ ...REPONSE, orientation_professionnel: true });

    await service.envoyer('Je veux un spécialiste');

    expect(service.messages().at(-1)!.orientationAnnuaire).toBe(true);
  });

  it('commence fermée, avec le message d’accueil de Titou', () => {
    expect(service.ouverte()).toBe(false);
    expect(service.messages()).toHaveLength(1);
    expect(service.messages()[0].auteur).toBe('BOT');
    expect(service.debutDeConversation()).toBe(true);
  });

  it('s’ouvre, se ferme et bascule', () => {
    service.ouvrir();
    expect(service.ouverte()).toBe(true);
    service.fermer();
    expect(service.ouverte()).toBe(false);
    service.basculer();
    expect(service.ouverte()).toBe(true);
    service.basculer();
    expect(service.ouverte()).toBe(false);
  });

  it('envoie le message, affiche la réponse et garde le numéro de conversation', async () => {
    envoyer.mockResolvedValue(REPONSE);

    await service.envoyer('  Je suis stressé  ');
    envoyer.mockResolvedValue({ ...REPONSE, reponse: 'Parlons-en.' });
    await service.envoyer('Au travail');

    expect(envoyer).toHaveBeenNthCalledWith(1, 'Je suis stressé', null, false, []);
    // Le deuxième envoi transmet l'échange précédent, sans le message d'accueil
    expect(envoyer).toHaveBeenNthCalledWith(2, 'Au travail', 42, false, [
      { auteur: 'UTILISATEUR', contenu: 'Je suis stressé' },
      { auteur: 'BOT', contenu: 'Je vous écoute.' },
    ]);
    expect(service.messages().map((m) => m.contenu).slice(1)).toEqual([
      'Je suis stressé',
      'Je vous écoute.',
      'Au travail',
      'Parlons-en.',
    ]);
    expect(service.debutDeConversation()).toBe(false);
    expect(service.enCours()).toBe(false);
  });

  it('ignore un message vide', async () => {
    await service.envoyer('   ');
    expect(envoyer).not.toHaveBeenCalled();
    expect(service.messages()).toHaveLength(1);
  });

  it('ne transmet que les 6 derniers échanges', async () => {
    envoyer.mockResolvedValue(REPONSE);
    for (let i = 1; i <= 5; i++) await service.envoyer(`Message ${i}`);

    await service.envoyer('Dernier');

    const historique = envoyer.mock.lastCall![3]!;
    expect(historique).toHaveLength(6);
    expect(historique.at(-1)).toEqual({ auteur: 'BOT', contenu: 'Je vous écoute.' });
    expect(historique.some((e) => e.contenu === 'Message 1')).toBe(false);
  });

  it('affiche les numéros d’urgence si le chatbot est indisponible', async () => {
    envoyer.mockRejectedValue(new Error('hors ligne'));

    await service.envoyer('Bonjour');

    const derniere = service.messages().at(-1)!;
    expect(derniere.auteur).toBe('BOT');
    expect(derniere.contenu).toContain('800 805 805');
    expect(service.enCours()).toBe(false);
  });

  it('ne demande la conservation que pour un compte utilisateur qui l’a accepté', async () => {
    envoyer.mockResolvedValue(REPONSE);
    await service.definirConservation(true);

    await service.envoyer('Visiteur');
    typeCompte.set('utilisateur');
    await service.envoyer('Utilisateur');

    expect(envoyer).toHaveBeenNthCalledWith(1, 'Visiteur', null, false, expect.any(Array));
    expect(envoyer).toHaveBeenNthCalledWith(2, 'Utilisateur', 42, true, expect.any(Array));
  });

  it('efface la conversation et ferme la fenêtre quand le compte change (déconnexion)', async () => {
    envoyer.mockResolvedValue(REPONSE);
    identifiant.set(7);
    TestBed.tick();
    typeCompte.set('utilisateur');
    service.ouvrir();
    await service.definirConservation(true);
    await service.envoyer('Message privé');

    identifiant.set(null);
    TestBed.tick();

    expect(service.ouverte()).toBe(false);
    expect(service.messages()).toHaveLength(1);
    expect(service.messages().some((m) => m.contenu === 'Message privé')).toBe(false);
    expect(service.consentementConservation()).toBe(false);

    await service.envoyer('Nouvelle conversation');
    // Nouvelle conversation : rien de l'ancienne n'est transmis
    expect(envoyer).toHaveBeenLastCalledWith('Nouvelle conversation', null, false, []);
  });

  describe('historique (compte utilisateur)', () => {
    beforeEach(() => {
      identifiant.set(7);
      typeCompte.set('utilisateur');
      TestBed.tick();
      envoyer.mockResolvedValue(REPONSE);
    });

    it('cocher la case en cours de route enregistre les messages déjà échangés', async () => {
      envoyer.mockResolvedValue({ ...REPONSE, conversation_id: null, urgence: true, ressource: { ressource_id: 3, titre: 'Respirer', thematique: 'Stress' } });
      await service.envoyer('Je panique');
      creer.mockResolvedValue(99);

      await service.definirConservation(true);

      expect(creer).toHaveBeenCalledWith([
        { auteur: 'UTILISATEUR', contenu: 'Je panique', urgence: false, ressource_id: null },
        { auteur: 'BOT', contenu: 'Je vous écoute.', urgence: true, ressource_id: 3 },
      ]);
      expect(service.idConversationAffichee()).toBe(99);

      envoyer.mockResolvedValue(REPONSE);
      await service.envoyer('Merci');
      expect(envoyer).toHaveBeenLastCalledWith('Merci', 99, true, expect.any(Array));
    });

    it('cocher la case avant tout message ne crée rien d’avance', async () => {
      await service.definirConservation(true);

      expect(creer).not.toHaveBeenCalled();
      expect(service.consentementConservation()).toBe(true);
    });

    it('décoche la case si l’enregistrement échoue', async () => {
      // Sans consentement, le backend ne renvoie pas de numéro de conversation
      envoyer.mockResolvedValue({ ...REPONSE, conversation_id: null });
      await service.envoyer('Bonjour');
      creer.mockRejectedValue(new Error('hors ligne'));

      await service.definirConservation(true);

      expect(service.consentementConservation()).toBe(false);
      expect(service.erreurConservation()).toBe(true);
    });

    it('charge la liste des conversations', async () => {
      lister.mockResolvedValue([{ id: 1, date: '', derniere_activite: '', nombre_messages: 2, apercu: 'Je dors mal' }]);

      const chargement = service.afficherHistorique();
      expect(service.vue()).toBe('historique');
      expect(service.etatHistorique()).toBe('chargement');
      await chargement;

      expect(service.etatHistorique()).toBe('pret');
      expect(service.historique().map((c) => c.apercu)).toEqual(['Je dors mal']);
    });

    it('signale une erreur de chargement de l’historique', async () => {
      lister.mockRejectedValue(new Error('hors ligne'));
      await service.afficherHistorique();
      expect(service.etatHistorique()).toBe('erreur');
    });

    it('reprend une conversation conservée et la continue', async () => {
      lire.mockResolvedValue({
        id: 5,
        date: '2026-09-27T10:00:00Z',
        messages: [
          { id: 1, auteur: 'UTILISATEUR', contenu: 'Je dors mal', date_envoi: '2026-09-27T10:00:00Z', urgence: false, ressource: null },
          { id: 2, auteur: 'BOT', contenu: 'Depuis quand ?', date_envoi: '2026-09-27T10:00:05Z', urgence: false, ressource: null },
        ],
      });
      await service.afficherHistorique();

      await service.reprendre(5);

      expect(service.vue()).toBe('conversation');
      expect(service.messages().map((m) => m.contenu).slice(1)).toEqual(['Je dors mal', 'Depuis quand ?']);
      expect(service.consentementConservation()).toBe(true);
      await service.envoyer('Depuis une semaine');
      // La conversation reprise sert de contexte à Titou
      expect(envoyer).toHaveBeenLastCalledWith('Depuis une semaine', 5, true, [
        { auteur: 'UTILISATEUR', contenu: 'Je dors mal' },
        { auteur: 'BOT', contenu: 'Depuis quand ?' },
      ]);
    });

    it('supprimer la conversation affichée repart d’une conversation vierge', async () => {
      lire.mockResolvedValue({ id: 5, date: '', messages: [{ id: 1, auteur: 'UTILISATEUR', contenu: 'Secret', date_envoi: '2026-09-27T10:00:00Z', urgence: false, ressource: null }] });
      lister.mockResolvedValue([{ id: 5, date: '', derniere_activite: '', nombre_messages: 1, apercu: 'Secret' }]);
      await service.afficherHistorique();
      await service.reprendre(5);
      supprimer.mockResolvedValue();

      await service.supprimer(5);

      expect(supprimer).toHaveBeenCalledWith(5);
      expect(service.historique()).toEqual([]);
      expect(service.messages()).toHaveLength(1);
      expect(service.idConversationAffichee()).toBeNull();
      expect(service.consentementConservation()).toBe(false);
    });
  });
});
