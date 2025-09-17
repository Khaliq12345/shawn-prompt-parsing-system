# Documentation de l'API - Shawn Prompt Parsing System

Cette documentation décrit l'API pour le système de parsing de prompts de Shawn.

## Authentification

Toutes les requêtes à l'API doivent inclure une clé d'API valide. La clé doit être passée dans l'en-tête `X-API-KEY`.

`curl -X GET "https://your-api-domain.com/api/llm/extract-brand-info?prompt_id=prompt-123&s3_key=path/to/your/file.txt" -H "X-API-KEY: VOTRE_CLE_API"`

## Réponses d'Erreur Courantes

L'API utilise les codes de statut HTTP standard pour indiquer le succès ou l'échec d'une requête.

-   **Code 403: Forbidden**
    -   **Cause**: La clé d'API (`X-API-KEY`) est manquante, invalide ou n'est pas autorisée à accéder à la ressource.
    -   **Réponse**: 
        ```json
        {
          "detail": "Invalid or missing API Key"
        }
        ```

-   **Code 404: Not Found**
    -   **Cause**: La ressource que vous essayez de récupérer n'existe pas. Cela peut se produire si le `prompt_id` ou le `process_id` est incorrect, ou si vous demandez le statut d'un processus qui n'a pas encore été démarré par le worker.
    -   **Réponse**: 
        ```json
        {
          "detail": "Not Found"
        }
        ```

-   **Code 500: Internal Server Error**
    -   **Cause**: Une erreur inattendue s'est produite sur le serveur. Cela peut être dû à un problème de connexion à la base de données, une erreur dans le service LLM, ou tout autre problème interne.
    -   **Réponse**: Le message de détail peut varier en fonction de l'erreur.
        ```json
        {
          "detail": "Error: <description de l'erreur>"
        }
        ```

## Endpoints

L'API est divisée en trois sections principales :

1.  **LLM**: Pour démarrer et suivre les tâches de traitement de langage naturel.
2.  **Logs**: Pour récupérer les journaux (logs) des processus.
3.  **Metrics**: Pour obtenir les métriques extraites des textes.

---

### LLM

Cette section concerne le démarrage et le suivi des tâches de traitement.

#### 1. Démarrer l'extraction d'informations sur la marque

Démarre une tâche asynchrone pour extraire les mentions de marque et d'autres informations pertinentes d'un texte source.

-   **URL**: `/api/llm/extract-brand-info`
-   **Méthode**: `GET`
-   **Paramètres de requête**:
    -   `prompt_id` (string, requis): Un identifiant unique pour le prompt.
    -   `s3_key` (string, requis): La clé de l'objet S3 contenant le texte à analyser.

-   **Exemple de requête**:

    ```bash
    curl -X GET "https://your-api-domain.com/api/llm/extract-brand-info?prompt_id=prompt-123&s3_key=path/to/your/file.txt" -H "X-API-KEY: VOTRE_CLE_API"
    ```

-   **Réponse réussie (200)**:

    ```json
    {
      "prompt_id": "prompt-123",
      "process_id": "prompt-123_1678886400",
      "details": "parsing started"
    }
    ```

#### 2. Obtenir le statut du processus

Récupère le statut d'une tâche d'extraction en cours ou terminée.

-   **URL**: `/api/llm/get-process-status`
-   **Méthode**: `GET`
-   **Paramètres de requête**:
    -   `prompt_id` (string, requis): L'identifiant du prompt.
    -   `process_id` (string, requis): L'identifiant du processus retourné by la première requête.

-   **Exemple de requête**:

    ```bash
    curl -X GET "https://your-api-domain.com/api/llm/get-process-status?prompt_id=prompt-123&process_id=prompt-123_1678886400" -H "X-API-KEY: VOTRE_CLE_API"
    ```

-   **Réponse réussie (200)**:

    Les statuts possibles sont `running`, `success`, ou `failed`.

    ```json
    {
      "prompt_id": "prompt-123",
      "process_id": "prompt-123_1678886400",
      "status": "success"
    }
    ```

---

### Logs

Cette section permet de récupérer les journaux d'un processus de traitement.

#### 1. Obtenir les logs

Récupère les journaux associés à un `prompt_id` spécifique.

-   **URL**: `/api/logs/{prompt_id}`
-   **Méthode**: `GET`
-   **Paramètre de chemin**:
    -   `prompt_id` (string, requis): L'identifiant du prompt.

-   **Exemple de requête**:

    ```bash
    curl -X GET "https://your-api-domain.com/api/logs/prompt-123" -H "X-API-KEY: VOTRE_CLE_API"
    ```

-   **Réponse réussie (200)**:

    ```json
    {
      "details": [
        "Log entry 1: Process started",
        "Log entry 2: Data loaded from S3",
        "Log entry 3: Analysis complete"
      ]
    }
    ```

---

### Metrics

Cette section fournit des points de terminaison pour récupérer les différentes métriques extraites du texte.

#### 1. Mentions de la marque

-   **URL**: `/api/metrics/brand-mentions`
-   **Méthode**: `GET`
-   **Paramètres**: `prompt_id`, `brand`
-   **Exemple de requête**:
    ```bash
    curl -X GET "https://your-api-domain.com/api/metrics/brand-mentions?prompt_id=prompt-123&brand=Nike" -H "X-API-KEY: VOTRE_CLE_API"
    ```
-   **Exemple de réponse réussie (200)**:
    ```json
    {
      "data": {
        "mentions": 12
      }
    }
    ```

#### 2. Part de voix de la marque (Share of Voice)

-   **URL**: `/api/metrics/brand-share-of-voice`
-   **Méthode**: `GET`
-   **Paramètres**: `prompt_id`, `brand`
-   **Exemple de requête**:
    ```bash
    curl -X GET "https://your-api-domain.com/api/metrics/brand-share-of-voice?prompt_id=prompt-123&brand=Nike" -H "X-API-KEY: VOTRE_CLE_API"
    ```
-   **Exemple de réponse réussie (200)**:
    ```json
    {
      "data": {
        "sov": 34.5
      }
    }
    ```

#### 3. Couverture de la marque

-   **URL**: `/api/metrics/brand-coverage`
-   **Méthode**: `GET`
-   **Paramètres**: `prompt_id`, `brand`
-   **Exemple de requête**:
    ```bash
    curl -X GET "https://your-api-domain.com/api/metrics/brand-coverage?prompt_id=prompt-123&brand=Nike" -H "X-API-KEY: VOTRE_CLE_API"
    ```
-   **Exemple de réponse réussie (200)**:
    ```json
    {
      "data": {
        "coverage": 65.34
      }
    }
    ```

#### 4. Position de la marque

-   **URL**: `/api/metrics/brand-position`
-   **Méthode**: `GET`
-   **Paramètres**: `prompt_id`, `brand`
-   **Exemple de requête**:
    ```bash
    curl -X GET "https://your-api-domain.com/api/metrics/brand-position?prompt_id=prompt-123&brand=Nike" -H "X-API-KEY: VOTRE_CLE_API"
    ```
-   **Exemple de réponse réussie (200)**:
    ```json
    {
      "data": {
        "position": 2.5
      }
    }
    ```

#### 5. Classement de la marque

-   **URL**: `/api/metrics/brand-ranking`
-   **Méthode**: `GET`
-   **Paramètres**: `prompt_id`
-   **Exemple de requête**:
    ```bash
    curl -X GET "https://your-api-domain.com/api/metrics/brand-ranking?prompt_id=prompt-123" -H "X-API-KEY: VOTRE_CLE_API"
    ```
-   **Exemple de réponse réussie (200)**:
    ```json
    {
      "data": {
        "ranking": [
          {
            "brand": "Adidas",
            "mention_count": 12,
            "rank": 1
          },
          {
            "brand": "Nike",
            "mention_count": 8,
            "rank": 2
          },
          {
            "brand": "Puma",
            "mention_count": 8,
            "rank": 2
          },
          {
            "brand": "Reebok",
            "mention_count": 3,
            "rank": 4
          }
        ]
      }
    }
    ```    