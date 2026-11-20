"""
test_film.py - Tests unitaires de film.py

Lancer avec :   python -m unittest test_film -v
ou avec pytest: pytest test_film.py

Principe d'un test unitaire :
  - on prépare des données
  - on appelle le code à tester
  - on vérifie le résultat avec une "assertion" (assertEqual, assertTrue...)
Un test réussit si aucune assertion n'échoue.
"""

import json
import unittest

# Exception levée quand on essaie de modifier un objet frozen
from dataclasses import FrozenInstanceError

# On importe ce qu'on veut tester depuis film.py
from film import Film, favoris_to_json, favoris_from_json


# Chaque classe de test regroupe des tests sur un même thème.
# Elle hérite de unittest.TestCase ; chaque méthode qui commence
# par "test_" est exécutée automatiquement.


# ======================================================================
# 1) CRÉATION ET VALIDATION
# ======================================================================
class TestCreation(unittest.TestCase):
    """Création d'un film valide et cas limites de validation."""

    def test_creation_valide(self):
        f = Film("Inception", "Christopher Nolan", 2010, 8.8)
        # assertEqual(a, b) vérifie que a == b
        self.assertEqual(f.titre, "Inception")
        self.assertEqual(f.annee, 2010)

    def test_note_bornes_acceptees(self):
        # Cas limites : 0 et 10 sont valides (bornes incluses).
        # Si le constructeur lève une exception, le test échoue.
        Film("A", "B", 2000, 0)
        Film("A", "B", 2000, 10)

    def test_note_entier_accepte(self):
        # Une note entière (8) est acceptée comme un float
        self.assertEqual(Film("A", "B", 2000, 8).note, 8)

    def test_note_hors_bornes(self):
        for note in (-0.1, 10.1, -5, 100):
            # subTest : si une valeur échoue, les autres sont quand même
            # testées, et le message d'erreur indique laquelle a échoué.
            with self.subTest(note=note):
                # assertRaises vérifie que le bloc LÈVE l'exception indiquée
                with self.assertRaises(ValueError):
                    Film("A", "B", 2000, note)

    def test_note_nan_refusee(self):
        # float("nan") = "not a number", valeur numérique spéciale
        with self.assertRaises(ValueError):
            Film("A", "B", 2000, float("nan"))

    def test_types_invalides(self):
        # Chaque tuple = (titre, realisateur, annee, note) avec UN type faux
        cas = [
            (None, "B", 2000, 5),     # valeur nulle pour le titre
            ("A", None, 2000, 5),     # valeur nulle pour le réalisateur
            (123, "B", 2000, 5),      # titre qui n'est pas une chaîne
            ("A", "B", "2000", 5),    # année donnée sous forme de texte
            ("A", "B", 2000.5, 5),    # année décimale
            ("A", "B", None, 5),      # année nulle
            ("A", "B", 2000, "5"),    # note donnée sous forme de texte
            ("A", "B", 2000, None),   # note nulle
            ("A", "B", True, 5),      # bool refusé comme année
            ("A", "B", 2000, True),   # bool refusé comme note
        ]
        for args in cas:
            with self.subTest(args=args):
                with self.assertRaises(TypeError):
                    # *args déballe le tuple en 4 arguments séparés
                    Film(*args)

    def test_chaines_vides(self):
        with self.assertRaises(ValueError):
            Film("", "B", 2000, 5)         # titre vide
        with self.assertRaises(ValueError):
            Film("A", "   ", 2000, 5)      # réalisateur : uniquement des espaces


# ======================================================================
# 2) IMMUABILITÉ (frozen=True) ET OPTIMISATION (slots=True)
# ======================================================================
class TestImmutabilite(unittest.TestCase):
    def test_modification_interdite(self):
        f = Film("A", "B", 2000, 5)
        with self.assertRaises(FrozenInstanceError):
            f.note = 9  # interdit car frozen=True

    def test_pas_de_nouvel_attribut(self):
        f = Film("A", "B", 2000, 5)
        # Ajouter un attribut inconnu échoue aussi.
        # Selon la version de Python, l'erreur peut varier : on accepte
        # donc plusieurs types d'exceptions.
        with self.assertRaises((FrozenInstanceError, AttributeError, TypeError)):
            f.autre = 1

    def test_slots_actif(self):
        f = Film("A", "B", 2000, 5)
        # Avec slots=True, l'objet n'a pas de dictionnaire interne __dict__
        self.assertFalse(hasattr(f, "__dict__"))

    def test_hashable(self):
        # frozen + eq => Python génère __hash__ : un Film peut être mis
        # dans un set ou servir de clé de dictionnaire.
        f1 = Film("A", "B", 2000, 5)
        f2 = Film("A", "B", 2000, 5)
        # Deux films identiques comptent pour UN seul élément dans le set
        self.assertEqual(len({f1, f2}), 1)


# ======================================================================
# 3) est_classique()
# ======================================================================
class TestEstClassique(unittest.TestCase):
    def test_avant_2000(self):
        # assertTrue(x) vérifie que x est vrai
        self.assertTrue(Film("A", "B", 1999, 5).est_classique())

    def test_annee_2000_pas_classique(self):
        # Cas limite : "avant 2000" est strict, donc 2000 donne False
        self.assertFalse(Film("A", "B", 2000, 5).est_classique())

    def test_apres_2000(self):
        self.assertFalse(Film("A", "B", 2015, 5).est_classique())


# ======================================================================
# 4) JSON : to_json et from_json
# ======================================================================
class TestJson(unittest.TestCase):
    def setUp(self):
        # setUp est exécutée AVANT chaque test : chaque test repart
        # d'un film de référence neuf.
        self.film = Film("Amélie", "Jean-Pierre Jeunet", 2001, 8.3)

    def test_to_json_contenu(self):
        # On relit le JSON en dictionnaire pour comparer le contenu
        # sans dépendre de l'ordre des clés ni des espaces.
        data = json.loads(self.film.to_json())
        self.assertEqual(data, {
            "titre": "Amélie",
            "realisateur": "Jean-Pierre Jeunet",
            "annee": 2001,
            "note": 8.3,
        })

    def test_to_json_garde_les_accents(self):
        # assertIn(a, b) vérifie que a est contenu dans b
        # (grâce à ensure_ascii=False, "é" n'est pas écrit \u00e9)
        self.assertIn("Amélie", self.film.to_json())

    def test_aller_retour(self):
        # Test "aller-retour" : Film -> JSON -> Film doit redonner
        # un film égal à l'original.
        self.assertEqual(Film.from_json(self.film.to_json()), self.film)

    def test_from_json_invalide(self):
        # Texte qui n'est pas du JSON
        with self.assertRaises(ValueError):
            Film.from_json("ceci n'est pas du json")

    def test_from_json_pas_un_objet(self):
        # JSON valide, mais c'est une liste et non un objet
        with self.assertRaises(ValueError):
            Film.from_json("[1, 2, 3]")

    def test_from_json_champ_manquant(self):
        # Il manque le champ "note"
        with self.assertRaises(ValueError):
            Film.from_json('{"titre": "A", "realisateur": "B", "annee": 2000}')

    def test_from_json_champ_inconnu(self):
        # Champ "x" en trop
        with self.assertRaises(ValueError):
            Film.from_json(
                '{"titre": "A", "realisateur": "B", "annee": 2000, "note": 5, "x": 1}'
            )

    def test_from_json_valeur_invalide(self):
        # La validation de __post_init__ s'applique aussi au chargement.
        # note = 50 : hors bornes -> ValueError
        with self.assertRaises(ValueError):
            Film.from_json('{"titre": "A", "realisateur": "B", "annee": 2000, "note": 50}')
        # annee = "2000" (texte) : mauvais type -> TypeError
        with self.assertRaises(TypeError):
            Film.from_json('{"titre": "A", "realisateur": "B", "annee": "2000", "note": 5}')

    def test_from_json_null(self):
        # En JSON, "null" devient None en Python : refusé pour le titre
        with self.assertRaises(TypeError):
            Film.from_json('{"titre": null, "realisateur": "B", "annee": 2000, "note": 5}')


# ======================================================================
# 5) COMPARAISON PAR NOTE
# ======================================================================
class TestComparaison(unittest.TestCase):
    def setUp(self):
        # Le titre "Z" vient APRÈS "A" alphabétiquement, mais sa note est
        # plus basse : ça permet de vérifier qu'on trie par note et pas par titre.
        self.bas = Film("Z", "R1", 1990, 4.0)
        self.haut = Film("A", "R2", 2020, 9.0)

    def test_operateurs(self):
        self.assertTrue(self.bas < self.haut)
        self.assertTrue(self.bas <= self.haut)
        self.assertTrue(self.haut > self.bas)
        self.assertTrue(self.haut >= self.bas)

    def test_tri_par_note_et_non_par_titre(self):
        # sorted() utilise __lt__ ; on attend [bas, haut] (note croissante)
        self.assertEqual(sorted([self.haut, self.bas]), [self.bas, self.haut])

    def test_notes_egales(self):
        a = Film("A", "R", 2000, 7.0)
        b = Film("B", "R", 2001, 7.0)
        # Même note : <= et >= vrais, < et > faux
        self.assertTrue(a <= b and a >= b)
        self.assertFalse(a < b or a > b)
        # Mais == compare TOUS les champs : ces films restent différents
        self.assertNotEqual(a, b)

    def test_comparaison_avec_autre_type(self):
        # Comparer un Film avec un entier n'a pas de sens : TypeError
        with self.assertRaises(TypeError):
            self.bas < 5


# ============================================
# ======================================================================
# 6) LISTE DE FAVORIS
# ======================================================================
class TestFavoris(unittest.TestCase):
    def test_aller_retour(self):
        films = [Film("A", "R1", 1999, 7.5), Film("B", "R2", 2010, 8)]
        # Liste -> JSON -> liste : on doit retrouver les mêmes films
        self.assertEqual(favoris_from_json(favoris_to_json(films)), films)

    def test_liste_vide(self):
        # Cas limite : aucune entrée
        self.assertEqual(favoris_to_json([]), "[]")
        self.assertEqual(favoris_from_json("[]"), [])

    def test_element_invalide_a_la_serialisation(self):
        # Un élément qui n'est pas un Film doit être refusé
        with self.assertRaises(TypeError):
            favoris_to_json([Film("A", "R", 2000, 5), "pas un film"])

    def test_json_pas_une_liste(self):
        # Un objet JSON seul n'est pas une liste de favoris
        with self.assertRaises(ValueError):
            favoris_from_json('{"titre": "A"}')

    def test_element_invalide_au_chargement(self):
        # Le premier film de la liste est incomplet
        with self.assertRaises(ValueError):
            favoris_from_json('[{"titre": "A"}]')


# Permet de lancer les tests avec : python test_film.py
if __name__ == "__main__":
    unittest.main()