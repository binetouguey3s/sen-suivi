#!/usr/bin/env python3
"""
Sen Suivi — Optimisation des images de la maquette.

Redimensionne, recadre et convertit en WebP les images telechargees,
selon la categorie deduite du nom de fichier.

Usage :
    python3 optimiser-images.py <dossier_source> <dossier_destination>

Exemple :
    python3 optimiser-images.py images-brutes/ frontend/src/assets/images/

Prerequis :
    pip install pillow
"""

import sys
from pathlib import Path

try:
    from PIL import Image, ImageOps
except ImportError:
    print("Pillow n'est pas installe. Lance : pip install pillow")
    sys.exit(1)


# Format cible selon le prefixe du nom de fichier
FORMATS = {
    "lieu-": (1600, 900),
    "pro-": (400, 400),
    "ressource-": (800, 450),
    "avatar-": (200, 200),
}
FORMAT_DEFAUT = (1200, 800)

# Sous-dossier de destination selon le prefixe
DOSSIERS = {
    "lieu-": "lieux",
    "pro-": "professionnels",
    "ressource-": "ressources",
    "avatar-": "avatars",
}

QUALITE_WEBP = 82
EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}


def categorie(nom: str):
    """Retourne (dimensions, sous-dossier) selon le prefixe du fichier."""
    for prefixe, taille in FORMATS.items():
        if nom.startswith(prefixe):
            return taille, DOSSIERS[prefixe]
    return FORMAT_DEFAUT, "divers"


def formater_poids(octets: int) -> str:
    return f"{octets / 1024:.0f} Ko" if octets < 1024 * 1024 else f"{octets / (1024 * 1024):.1f} Mo"


def traiter(fichier: Path, racine_sortie: Path) -> tuple[int, int]:
    """Traite une image. Retourne (poids avant, poids apres)."""
    nom = fichier.stem.lower()
    taille, sous_dossier = categorie(nom)

    destination = racine_sortie / sous_dossier
    destination.mkdir(parents=True, exist_ok=True)
    sortie = destination / f"{nom}.webp"

    poids_avant = fichier.stat().st_size

    with Image.open(fichier) as img:
        # Corrige l'orientation EXIF des photos prises au telephone
        img = ImageOps.exif_transpose(img)
        img = img.convert("RGB")
        # Recadre au centre, au ratio demande, sans deformer
        img = ImageOps.fit(img, taille, Image.LANCZOS, centering=(0.5, 0.4))
        img.save(sortie, "WEBP", quality=QUALITE_WEBP, method=6)

    poids_apres = sortie.stat().st_size
    gain = 100 - (poids_apres / poids_avant * 100)

    print(
        f"  {fichier.name:<42} -> {sous_dossier}/{sortie.name:<38} "
        f"{taille[0]}x{taille[1]:<6} {formater_poids(poids_avant):>9} -> "
        f"{formater_poids(poids_apres):>9}  ({gain:+.0f} %)"
    )
    return poids_avant, poids_apres


def main() -> None:
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)

    source = Path(sys.argv[1])
    sortie = Path(sys.argv[2])

    if not source.is_dir():
        print(f"Dossier source introuvable : {source}")
        sys.exit(1)

    fichiers = sorted(
        f for f in source.iterdir()
        if f.is_file() and f.suffix.lower() in EXTENSIONS
    )

    if not fichiers:
        print(f"Aucune image trouvee dans {source}")
        sys.exit(0)

    print(f"\n{len(fichiers)} image(s) a traiter\n")

    total_avant = total_apres = 0
    erreurs = []

    for fichier in fichiers:
        try:
            avant, apres = traiter(fichier, sortie)
            total_avant += avant
            total_apres += apres
        except Exception as erreur:
            erreurs.append((fichier.name, erreur))
            print(f"  {fichier.name:<42} ECHEC : {erreur}")

    print(f"\nTotal : {formater_poids(total_avant)} -> {formater_poids(total_apres)}", end="")
    if total_avant:
        print(f"  ({100 - total_apres / total_avant * 100:+.0f} %)")
    else:
        print()

    if erreurs:
        print(f"\n{len(erreurs)} echec(s) :")
        for nom, erreur in erreurs:
            print(f"  - {nom} : {erreur}")

    print(
        "\nPense a renseigner docs/CREDITS-IMAGES.md : "
        "certaines licences exigent l'attribution.\n"
    )


if __name__ == "__main__":
    main()
