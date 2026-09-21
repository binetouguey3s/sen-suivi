#!/usr/bin/env bash
# =====================================================================
#  Sen Suivi — vérification complète : back-end, IA, n8n, front-end
#
#  Usage, depuis la racine du projet :
#      bash verifier-sen-suivi.sh            # tout tester
#      bash verifier-sen-suivi.sh backend    # une seule partie
#  Parties : services, backend, ia, n8n, frontend
# =====================================================================

set -u
PARTIE="${1:-tout}"

BACK="http://localhost:8000"
IA="http://localhost:8001"
N8N="http://localhost:5678"
FRONT="http://localhost:4200"

OK=0; KO=0; AVERT=0
vert()   { printf "  \033[32m✅ %s\033[0m\n" "$1"; OK=$((OK+1)); }
rouge()  { printf "  \033[31m❌ %s\033[0m\n" "$1"; KO=$((KO+1)); }
jaune()  { printf "  \033[33m⚠️  %s\033[0m\n" "$1"; AVERT=$((AVERT+1)); }
titre()  { printf "\n\033[1;34m━━━ %s ━━━\033[0m\n" "$1"; }
detail() { printf "     \033[90m%s\033[0m\n" "$(echo "$1" | head -c 300)"; }

code_http() { curl -s -o /dev/null -w "%{http_code}" --max-time 20 "$@"; }
lire_env()  { grep -E "^$1=" .env 2>/dev/null | head -1 | cut -d= -f2-; }
json()      { python3 -c "import sys,json; d=json.load(sys.stdin); print($1)" 2>/dev/null; }

attendre_code() {  # attendre_code "libellé" "code attendu" curl-args...
  local lib="$1" att="$2"; shift 2
  local c; c=$(code_http "$@")
  if [[ "$att" == *"$c"* ]]; then vert "$lib ($c)"; else rouge "$lib — attendu $att, obtenu $c"; fi
}

[ -f docker-compose.yml ] || { echo "Lance ce script depuis la racine du projet."; exit 1; }
[ -f .env ] || { echo "Fichier .env absent : cp .env.example .env"; exit 1; }

# ---------------------------------------------------------------------
if [[ "$PARTIE" == "tout" || "$PARTIE" == "services" ]]; then
titre "0. SERVICES DOCKER"
for s in db backend ai-service frontend n8n; do
  etat=$(docker compose ps --format '{{.Service}} {{.State}}' 2>/dev/null | awk -v s="$s" '$1==s{print $2}')
  if [ "$etat" == "running" ]; then vert "$s tourne"
  elif [ -z "$etat" ]; then rouge "$s absent — docker compose up -d $s"
  else rouge "$s est « $etat » — docker compose logs $s --tail 30"; fi
done
if docker compose exec -T db pg_isready -U "$(lire_env POSTGRES_USER)" >/dev/null 2>&1; then
  vert "PostgreSQL accepte les connexions"
else rouge "PostgreSQL ne répond pas"; fi
fi

# ---------------------------------------------------------------------
if [[ "$PARTIE" == "tout" || "$PARTIE" == "backend" ]]; then
titre "1. BACK-END DJANGO"

attendre_code "Admin Django accessible"            "200 301 302" "$BACK/admin/"
attendre_code "Ressources publiques, sans compte"   "200" "$BACK/api/ressources"
attendre_code "Lieux publics, sans compte"          "200" "$BACK/api/lieux"
attendre_code "Journal d'humeur protégé sans jeton" "401 403" "$BACK/api/suivi-humeur"

n=$(curl -s "$BACK/api/ressources" | json "len(d['results'] if isinstance(d,dict) else d)")
if [ -n "$n" ] && [ "$n" -ge 1 ]; then vert "$n ressource(s) en base"
else rouge "Aucune ressource — charge les fixtures"; fi

demo=$(curl -s "$BACK/api/ressources" | grep -c "Contenu de démonstration")
[ "$demo" -gt 0 ] && jaune "Des ressources ont encore un contenu de démonstration"

# Compte de test jetable
EMAIL="test.$(date +%s)@sensuivi.sn"; MDP="MotDePasse!2026"
corps=$(curl -s -X POST "$BACK/api/auth/register" -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$MDP\",\"nom\":\"Test\",\"prenom\":\"Awa\"}")
if echo "$corps" | grep -qiE "email|id"; then vert "Inscription d'un utilisateur"
else rouge "Inscription — vérifie les champs attendus"; detail "$corps"; fi

reponse=$(curl -s -X POST "$BACK/api/auth/login" -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$MDP\"}")
JETON=$(echo "$reponse" | json "d.get('access','')")
if [ -n "$JETON" ]; then
  vert "Connexion, jeton JWT obtenu"
  type=$(python3 - "$JETON" <<'PY'
import sys, json, base64
p = sys.argv[1].split('.')[1]; p += '=' * (-len(p) % 4)
print(json.loads(base64.urlsafe_b64decode(p)).get('type_compte',''))
PY
)
  if [ -n "$type" ]; then vert "Claim type_compte présent dans le JWT : $type"
  else rouge "Claim type_compte absent du JWT"; fi

  AUTH=(-H "Authorization: Bearer $JETON")
  attendre_code "Journal d'humeur accessible avec jeton" "200" "${AUTH[@]}" "$BACK/api/suivi-humeur"

  c=$(code_http -X POST "$BACK/api/suivi-humeur" "${AUTH[@]}" -H "Content-Type: application/json" \
      -d '{"score_humeur":"BIEN","note":"Test automatique"}')
  if [[ "$c" == "200" || "$c" == "201" ]]; then vert "Enregistrement d'une humeur ($c)"
  else rouge "Enregistrement d'une humeur ($c)"
       detail "$(curl -s -X POST "$BACK/api/suivi-humeur" "${AUTH[@]}" -H 'Content-Type: application/json' -d '{"score_humeur":"BIEN"}')"; fi

  for t in STRESS ANXIETE FATIGUE; do
    attendre_code "Questions d'auto-évaluation $t" "200" "${AUTH[@]}" "$BACK/api/auto-evaluations/questions/$t"
  done
else
  rouge "Connexion impossible"; detail "$reponse"
fi

echo "  … tests unitaires Django"
if docker compose exec -T backend python manage.py test --noinput >/tmp/tests_django.txt 2>&1; then
  vert "Tests unitaires Django : $(grep -oE 'Ran [0-9]+ tests?' /tmp/tests_django.txt)"
else rouge "Tests unitaires Django en échec — cat /tmp/tests_django.txt"; fi
fi

# ---------------------------------------------------------------------
if [[ "$PARTIE" == "tout" || "$PARTIE" == "ia" ]]; then
titre "2. INTELLIGENCE ARTIFICIELLE"

attendre_code "Microservice IA — /sante" "200" "$IA/sante"
detail "$(curl -s --max-time 20 "$IA/sante")"

[ "$(lire_env LLM_ACTIVE)" == "false" ] && jaune "LLM_ACTIVE=false : génération désactivée"
[ -z "$(lire_env LLM_CLE_API)" ] && jaune "LLM_CLE_API vide dans .env"

tester_message() {  # tester_message "message" "intention attendue ou URGENCE"
  local r; r=$(curl -s --max-time 25 -X POST "$BACK/api/chatbot/message" \
      -H "Content-Type: application/json" -d "{\"contenu\":\"$1\"}")
  local intention urgence source
  intention=$(echo "$r" | json "d.get('intention','')")
  urgence=$(echo "$r"   | json "d.get('urgence',False)")
  source=$(echo "$r"    | json "d.get('source_reponse','')")
  if [ "$2" == "URGENCE" ]; then
    if [ "$urgence" == "True" ]; then vert "« $1 » → urgence déclenchée"
    else rouge "« $1 » → urgence NON déclenchée"; detail "$r"; fi
  elif [ "$intention" == "$2" ]; then vert "« $1 » → $intention · source $source"
  elif [ -n "$intention" ]; then jaune "« $1 » → $intention (attendu $2) · source $source"
  else rouge "« $1 » → pas de réponse exploitable"; detail "$r"; fi
}

echo "  … chatbot, via l'API publique Django, sans compte"
tester_message "BONJOUR"                          "SALUTATION"
tester_message "JE SUIS MALADE"                   "SANTE_PHYSIQUE"
tester_message "je suis fatiguée"                 "FATIGUE"
tester_message "Je suis stressé par le boulot"    "STRESS"
tester_message "je narrive plus a dormir la nuit" "SOMMEIL"
tester_message "je cherche un psychologue"        "CHERCHER_PROFESSIONNEL"
tester_message "je veux que tout s'arrête, je n'en peux plus" "URGENCE"

echo "  … tests unitaires du microservice"
if docker compose exec -T ai-service python -m pytest -q >/tmp/tests_ia.txt 2>&1; then
  vert "Tests IA : $(tail -1 /tmp/tests_ia.txt)"
else rouge "Tests IA en échec — cat /tmp/tests_ia.txt"; fi

if docker compose exec -T ai-service test -f scripts/evaluer_intentions.py 2>/dev/null; then
  taux=$(docker compose exec -T ai-service python scripts/evaluer_intentions.py 2>/dev/null \
         | grep -oE '[0-9]+([.,][0-9]+)? ?%' | tail -1)
  [ -n "$taux" ] && vert "Taux de bonne classification : $taux" || jaune "Évaluation lancée, taux non lu"
else jaune "scripts/evaluer_intentions.py absent"; fi

if docker compose exec -T ai-service test -f scripts/verifier_llm.py 2>/dev/null; then
  echo "  … disponibilité des modèles Groq"
  docker compose exec -T ai-service python scripts/verifier_llm.py 2>&1 | sed 's/^/     /' | head -20
else jaune "scripts/verifier_llm.py absent"; fi
fi

# ---------------------------------------------------------------------
if [[ "$PARTIE" == "tout" || "$PARTIE" == "n8n" ]]; then
titre "3. AUTOMATISATIONS n8n"

attendre_code "n8n en ligne — /healthz" "200" "$N8N/healthz"

CLE=$(lire_env N8N_API_KEY)
if [ -z "$CLE" ]; then
  jaune "N8N_API_KEY absent du .env : liste des workflows non vérifiée"
else
  wf=$(curl -s --max-time 15 "$N8N/api/v1/workflows" -H "X-N8N-API-KEY: $CLE")
  total=$(echo "$wf"  | json "len(d.get('data',[]))")
  actifs=$(echo "$wf" | json "sum(1 for w in d.get('data',[]) if w.get('active'))")
  if [ -n "$total" ]; then
    [ "$total" -ge 3 ] && vert "$total workflow(s) dans n8n" || rouge "$total workflow(s) — il en faut 3"
    [ "${actifs:-0}" -ge 3 ] && vert "$actifs workflow(s) actif(s)" || rouge "${actifs:-0} actif(s) — active-les dans n8n"
    echo "$wf" | json "'\n'.join('     • '+('actif   ' if w.get('active') else 'INACTIF ')+w['name'] for w in d.get('data',[]))"
  else rouge "API n8n inaccessible — clé invalide ?"; detail "$wf"; fi
fi

nb=$(ls automations/*.json 2>/dev/null | wc -l)
[ "$nb" -ge 3 ] && vert "$nb export(s) JSON dans automations/" || jaune "$nb export(s) JSON dans automations/ — il en faut 3"
fi

# ---------------------------------------------------------------------
if [[ "$PARTIE" == "tout" || "$PARTIE" == "frontend" ]]; then
titre "4. FRONT-END ANGULAR"

attendre_code "Application servie sur le port 4200" "200" "$FRONT/"
for r in / /connexion /ressources /lieux /chatbot; do
  attendre_code "Route $r" "200" "$FRONT$r"
done

hex=$(grep -rEn "#[0-9A-Fa-f]{6}\b" frontend/src/app --include=*.scss --include=*.ts --include=*.html 2>/dev/null \
      | grep -v "tokens.scss" | wc -l)
[ "$hex" -eq 0 ] && vert "Aucune couleur hexadécimale en dur hors tokens.scss" \
                 || jaune "$hex couleur(s) hexadécimale(s) en dur hors tokens.scss"

lucide=$(grep -rln "from 'lucide-angular'" frontend/src/app 2>/dev/null | grep -v "core/icons" | wc -l)
[ "$lucide" -eq 0 ] && vert "Icônes importées uniquement via le registre" \
                    || jaune "$lucide fichier(s) importent lucide-angular directement"

grep -rq "gsk_" frontend/src 2>/dev/null && rouge "Une clé Groq apparaît dans le front-end !" \
                                         || vert "Aucune clé d'API dans le front-end"

echo "  … compilation de production (1 à 3 minutes)"
if docker compose exec -T frontend npx ng build >/tmp/build_front.txt 2>&1; then
  vert "Compilation de production réussie"
else rouge "Compilation en échec — tail -30 /tmp/build_front.txt"; fi
fi

# ---------------------------------------------------------------------
titre "SÉCURITÉ"
git check-ignore -q .env && vert ".env ignoré par Git" || rouge ".env N'EST PAS ignoré par Git"
git ls-files | grep -qE "^\.env$" && rouge ".env est versionné !" || vert ".env absent du dépôt"
grep -rqE "gsk_[A-Za-z0-9]{10,}" --include=*.py --include=*.ts --include=*.yml . 2>/dev/null \
  && rouge "Une clé Groq apparaît dans le code" || vert "Aucune clé Groq dans le code"

# ---------------------------------------------------------------------
printf "\n\033[1m━━━ BILAN : \033[32m%d réussi(s)\033[0m\033[1m · \033[31m%d échec(s)\033[0m\033[1m · \033[33m%d avertissement(s)\033[0m\n\n" "$OK" "$KO" "$AVERT"
[ "$KO" -eq 0 ]