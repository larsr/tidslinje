Tredjepartsbibliotek som sidan läser in. De ligger här i stället för på ett CDN
så att sidan och röktestet fungerar utan nät mot andra värdar.

Versioner, källfiler, licenser och kontrollsummor står i `libs.yaml`.
`uv run scripts/audit_vendor.py` kontrollerar kontrollsummorna och söker efter
kända sårbarheter i OSV; CI kör det vid varje push och en gång i veckan.
