---
id: 290
status: review
who: Claude
due_date: 
position: 1
created_at: 2026-05-08T23:52:00
updated_at: 2026-05-09T00:03:44
---

# QUALITY / SonarCloud

Met en place le sonar scanner dans les gh action
https://sonarcloud.io/project/configuration/AutoScan?id=lduchosal_jeff

---

## Resolution

### sonar-project.properties

- projectKey=lduchosal_jeff
- organization=lduchosal
- sources=src, tests=tests
- Python 3.11/3.12/3.13
- Coverage via coverage.xml
- Exclusions : badge SVG, htmlcov, dist, build, __pycache__

### Integration CI

Job sonarcloud dans python-package.yml :
1. Attend le job build (needs: build)
2. Checkout avec fetch-depth: 0 (pour git blame)
3. Download coverage.xml artifact
4. SonarSource/sonarqube-scan-action@v6

Necessite secret SONAR_TOKEN dans les settings du repo GitHub.
