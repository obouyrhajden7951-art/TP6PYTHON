"""
film.py - TP 6 : Dataclasses, Exercice 2
Nécessite Python 3.10+ (slots=True).
"""

from dataclasses import dataclass, asdict
import json


# frozen=True : objet immuable (modification interdite après création)
# slots=True  : pas de __dict__ par objet, donc moins de mémoire
@dataclass(frozen=True, slots=True)
class Film:
    """Représente un film du catalogue."""

    # Champs : l'ordre = l'ordre des arguments du constructeur
    titre: str
    realisateur: str
    annee: int
    note: float  # entre 0 et 10

    def __post_init__(self):
        """Appelée automatiquement après __init__ : valide les données."""

        # titre et realisateur : chaînes non vides
        for nom in ("titre", "realisateur"):
            valeur = getattr(self, nom)  # équivaut à self.titre / self.realisateur
            if not isinstance(valeur, str):
                raise TypeError(
                    f"{nom} doit être une chaîne (reçu : {type(valeur).__name__})"
                )
            if not valeur.strip():  # refuse "" et "   "
                raise ValueError(f"{nom} ne peut pas être vide")

        # annee : entier (bool exclu car True == 1 en Python)
        if not isinstance(self.annee, int) or isinstance(self.annee, bool):
            raise TypeError(
                f"annee doit être un entier (reçu : {type(self.annee).__name__})"
            )

        # note : int ou float, mais pas bool ni str
        if not isinstance(self.note, (int, float)) or isinstance(self.note, bool):
            raise TypeError(
                f"note doit être un nombre (reçu : {type(self.note).__name__})"
            )

        # note entre 0 et 10 (NaN est aussi refusé car 0 <= nan <= 10 est False)
        if not (0 <= self.note <= 10):
            raise ValueError(f"note doit être entre 0 et 10 (reçu : {self.note})")

    def est_classique(self) -> bool:
        """True si le film est sorti strictement avant 2000."""
        return self.annee < 2000

    def to_json(self) -> str:
        """Film -> texte JSON. ensure_ascii=False garde les accents."""
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_json(cls, texte: str) -> "Film":
        """Texte JSON -> Film (constructeur alternatif)."""
        donnees = json.loads(texte)  # JSON invalide -> JSONDecodeError (ValueError)

        if not isinstance(donnees, dict):
            raise ValueError("Le JSON doit représenter un objet (dictionnaire)")

        attendus = {"titre", "realisateur", "annee", "note"}

        manquants = attendus - donnees.keys()
        if manquants:
            raise ValueError(f"Champs manquants : {sorted(manquants)}")

        inconnus = donnees.keys() - attendus
        if inconnus:
            raise ValueError(f"Champs inconnus : {sorted(inconnus)}")

        # **donnees déballe le dict en arguments nommés ; __post_init__ valide
        return cls(**donnees)

    # Comparaison par NOTE (order=True comparerait d'abord le titre).
    # __eq__ reste celui de dataclass : égalité sur tous les champs.
    def __lt__(self, autre):
        if not isinstance(autre, Film):
            return NotImplemented
        return self.note < autre.note

    def __le__(self, autre):
        if not isinstance(autre, Film):
            return NotImplemented
        return self.note <= autre.note

    def __gt__(self, autre):
        if not isinstance(autre, Film):
            return NotImplemented
        return self.note > autre.note

    def __ge__(self, autre):
        if not isinstance(autre, Film):
            return NotImplemented
        return self.note >= autre.note


# ATTENTION : les deux fonctions ci-dessous sont au bord GAUCHE (pas
# indentées), donc en dehors de la classe Film. C'est ce qui les rend
# importables avec : from film import favoris_to_json
def favoris_to_json(films) -> str:
    """Séquence de Film -> une seule chaîne JSON (liste d'objets)."""
    liste = []
    for film in films:
        if not isinstance(film, Film):
            raise TypeError("Tous les éléments doivent être des Film")
        liste.append(asdict(film))
    return json.dumps(liste, ensure_ascii=False)


def favoris_from_json(texte: str) -> list:
    """Chaîne JSON (liste) -> liste de Film."""
    donnees = json.loads(texte)
    if not isinstance(donnees, list):
        raise ValueError("Le JSON doit représenter une liste")
    return [Film.from_json(json.dumps(element)) for element in donnees]


if __name__ == "__main__":
    f = Film("Le Parrain", "Francis Ford Coppola", 1972, 9.2)
    print(f.to_json())
    print("Classique ?", f.est_classique())