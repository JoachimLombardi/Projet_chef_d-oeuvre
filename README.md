# 🚀 Projet Chef d'Œuvre

<div align="center">
  <a href="https://media.licdn.com/dms/image/v2/D5612AQGgBoGZVp7XxA/article-cover_image-shrink_720_1280/article-cover_image-shrink_720_1280/0/1705242357114?e=1744243200&v=beta&t=68SvDGLDdBd0EIgvVtvfCbDXlYsybQBweopL5CnMtXs">
    <img src="https://media.licdn.com/dms/image/v2/D5612AQGgBoGZVp7XxA/article-cover_image-shrink_720_1280/article-cover_image-shrink_720_1280/0/1705242357114?e=1744243200&v=beta&t=68SvDGLDdBd0EIgvVtvfCbDXlYsybQBweopL5CnMtXs" alt="Logo" width="700" height="400">
  </a>
  <h3>RAG sur des Résumés PubMed 📚</h3>
  <p>
    Cette application permet de poser des questions sur des résumés PubMed, d'afficher la liste des articles avec les auteurs et affiliations correspondantes. Elle offre également une fonctionnalité pour évaluer la qualité de la recherche et de la génération en faisant varier certains paramètres. Un monitoring a été mis en place accessible via le menu de l'application.
  </p>
</div>

---

## 📑 Table des matières:

1. [Démarrer 🚀](#démarrer)
   - [Prérequis ⚙️](#prérequis)
   - [Installation 💻](#installation)
2. [Usage 🎯](#usage)
3. [Roadmap 🛤️](#roadmap)
4. [Built With 🛠️](#built-with)
5. [Contributions 🤝](#contributions)
6. [License 📄](#license)
7. [Contact 📬](#contact)
8. [Badges du projet 🏅](#badges-du-projet)

---

## 🚀 Démarrer 

Assurez-vous de disposer de [Docker](https://www.docker.com/) pour faire fonctionner ce projet.

### ⚙️ Prérequis

Vous aurez besoin d'une clé API pour certains services comme OpenAI. Il est conseillé de disposer d'un ordinateur avec 32 Go de RAM.

### 💻 Installation

1. Clonez le repo avec la commande :
   ```sh
   git clone https://github.com/JoachimLombardi/Projet_chef_d-oeuvre.git

2. Avant de lancer l'application, assurez-vous que vous avez configuré les variables d'environnement nécessaires.
   Créer un fichier .env dans le dossier `pubmed_analyze/docker` sur le modèle suivant:
```env
# Base de données PostgreSQL
DATABASE_NAME=pubmed
DATABASE_USER=postgres
DATABASE_PASSWORD=simplon2024
DATABASE_HOST=db
DATABASE_PORT=5432

# Clés API externes
OPENAI_API_KEY=your_openai_api_key_here  # Remplacez par votre clé API OpenAI
HUGGING_FACE_HUB_TOKEN=your_hugging_face_token_here  # Remplacez par votre jeton Hugging Face

# Configuration de l'email
EMAIL_HOST_USER=your_email_address_here  # Remplacez par l'adresse email utilisée pour envoyer les emails via Django
EMAIL_HOST_PASSWORD=your_email_password_here  # Remplacez par le mot de passe de votre adresse email

# Paramètres de Django
SECRET_KEY=your_django_secret_key_here  # Remplacez par une clé secrète unique pour votre projet Django
DEBUG=True  # Laissez à True pour le développement, passez à False pour la production
ALLOWED_HOSTS=localhost,127.0.0.1,django,db  # Laissez tel quel ou ajoutez d'autres hôtes autorisés

# URL de connexion à la base de données (si utilisée)
DATABASE_URL=postgres://postgres:simplon2024@db:5432/pubmed
```
3. Lancer le client Docker
4. Supprimer le fichier `postgresql` dans `pubmed_analyze\docker\data\postgresql`
5. Dans le terminal tapez:
   ```sh
   docker-compose --env-file .env up --build
   ```
6. Dans un navigateur, tapez l'URL suivante pour accéder à l'application:
   http://localhost:8000/article/read/

<p align="right">(<a href="#readme-top">back to top</a>)</p>



## 🎯 Usage
### Poser des questions au RAG (Retrieval Augmented Generation)

Vous pouvez poser des questions variées à l'application RAG, telles que :

- **Quels ont été les principaux résultats de l'étude qualitative explorant les expériences et la compréhension des patients concernant la sclérose en plaques (SEP) ?**
- **Quelles sont les conclusions concernant les lésions nouvellement apparues dans la sclérose en plaques (SEP) et leur évolution vers des lésions à expansion lente (SEL) dans le contexte du traitement au fingolimod ?**
- **Comment l'intelligence artificielle (IA) et l'apprentissage automatique (AA) peuvent-ils améliorer le diagnostic et la prédiction de la sclérose en plaques (SEP), et quels défis sont associés à leur mise en œuvre ?**

Après avoir posé une question, le RAG renverra une **réponse détaillée** dans un **cadre de réponse** ci-dessous, ainsi qu'une liste des **trois premiers articles** utilisés pour générer la réponse, dans un **cadre distinct**.

#### Exemple de question:

##### Cadre de question: 

![image](https://github.com/user-attachments/assets/82ee020c-6ee1-44c4-89c7-6d50153a293b)

#### Exemple de réponse :

##### Cadre de réponse :

![image](https://github.com/user-attachments/assets/c0b4f4aa-2fe8-419f-a9d3-a12df77c2b35)



<p align="right">(<a href="#readme-top">back to top</a>)</p>



## 🛤️ Roadmap


- [x] [Mettre en place Django](https://github.com/JoachimLombardi/Projet_chef_d-oeuvre/issues/1)  
- [x] [Création de la base de données](https://github.com/JoachimLombardi/Projet_chef_d-oeuvre/issues/2)  
- [x] [Scrapping](https://github.com/JoachimLombardi/Projet_chef_d-oeuvre/issues/3)  
- [x] [Insertion en base de données](https://github.com/JoachimLombardi/Projet_chef_d-oeuvre/issues/4)  
- [x] [READ](https://github.com/JoachimLombardi/Projet_chef_d-oeuvre/issues/5)  
- [x] [CREATE AND UPDATE](https://github.com/JoachimLombardi/Projet_chef_d-oeuvre/issues/6)  
- [x] [DELETE](https://github.com/JoachimLombardi/Projet_chef_d-oeuvre/issues/7)  
- [x] [RAG: Recherche](https://github.com/JoachimLombardi/Projet_chef_d-oeuvre/issues/8)  
- [x] [RAG: Génération](https://github.com/JoachimLombardi/Projet_chef_d-oeuvre/issues/9)  
- [x] [Tests](https://github.com/JoachimLombardi/Projet_chef_d-oeuvre/issues/10)  
- [x] [Monitoring](https://github.com/JoachimLombardi/Projet_chef_d-oeuvre/issues/11)  
- [x] [Evaluation du RAG](https://github.com/JoachimLombardi/Projet_chef_d-oeuvre/issues/12)  
- [x] [Gestion des utilisateurs](https://github.com/JoachimLombardi/Projet_chef_d-oeuvre/issues/13)  
- [x] [Gestion des erreurs](https://github.com/JoachimLombardi/Projet_chef_d-oeuvre/issues/14)  
- [x] [Optimisation du code](https://github.com/JoachimLombardi/Projet_chef_d-oeuvre/issues/15)  
- [x] [Conteneurisation](https://github.com/JoachimLombardi/Projet_chef_d-oeuvre/issues/16)  
- [x] [CI/CD](https://github.com/JoachimLombardi/Projet_chef_d-oeuvre/issues/17)  
- [ ] [Déploiements](https://github.com/JoachimLombardi/Projet_chef_d-oeuvre/issues/18)  
- [ ] [Futures améliorations](https://github.com/JoachimLombardi/Projet_chef_d-oeuvre/issues/19)  
  



Voir les [tâches](https://github.com/JoachimLombardi/Projet_chef_d-oeuvre/issues) pour une liste complète des tâches.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## 🛠️ Built With

<p align="left">
  <a href="https://www.djangoproject.com/" style="text-decoration: none;">
    <img src="https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white" alt="Django">
  </a>
  <a href="https://www.python.org/" style="text-decoration: none;">
    <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  </a>
  <a href="https://developer.mozilla.org/en-US/docs/Web/HTML" style="text-decoration: none;">
    <img src="https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white" alt="HTML">
  </a>
  <a href="https://www.postgresql.org/" style="text-decoration: none;">
    <img src="https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL">
  </a>
  <a href="https://www.elastic.co/" style="text-decoration: none;">
    <img src="https://img.shields.io/badge/Elasticsearch-005571?style=for-the-badge&logo=elasticsearch&logoColor=white" alt="Elasticsearch">
  </a>
  <a href="https://mistral.ai/" style="text-decoration: none;">
    <img src="https://img.shields.io/badge/Mistral_AI-FF6F61?style=for-the-badge&logo=mistral&logoColor=white" alt="Mistral AI">
  </a>
  <a href="https://openai.com/" style="text-decoration: none;">
    <img src="https://img.shields.io/badge/GPT-412991?style=for-the-badge&logo=openai&logoColor=white" alt="GPT">
  </a>
  <a href="https://grafana.com/" style="text-decoration: none;">
    <img src="https://img.shields.io/badge/Grafana-F46800?style=for-the-badge&logo=grafana&logoColor=white" alt="Grafana">
  </a>
  <a href="https://prometheus.io/" style="text-decoration: none;">
    <img src="https://img.shields.io/badge/Prometheus-E6522C?style=for-the-badge&logo=prometheus&logoColor=white" alt="Prometheus">
  </a>
  <a href="https://ollama.com/" style="text-decoration: none;">
    <img src="https://img.shields.io/badge/Ollama-000000?style=for-the-badge" alt="Ollama">
  </a>
  <a href="https://github.com/louislam/uptime-kuma" style="text-decoration: none;">
    <img src="https://img.shields.io/badge/Uptime%20Kuma-0078D7?style=for-the-badge" alt="Uptime Kuma">
  </a>
  <a href="https://developer.mozilla.org/fr/docs/Web/JavaScript" style="text-decoration: none;">
    <img src="https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black" alt="JavaScript">
  </a>
  <a href="https://developer.mozilla.org/fr/docs/Web/CSS" style="text-decoration: none;">
    <img src="https://img.shields.io/badge/CSS-1572B6?style=for-the-badge&logo=css3&logoColor=white" alt="CSS">
  </a>
  <a href="https://www.gnu.org/software/bash/" style="text-decoration: none;">
    <img src="https://img.shields.io/badge/Shell-4EAA25?style=for-the-badge&logo=gnu-bash&logoColor=white" alt="Shell">
  </a>
</p>


<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- CONTRIBUTING -->
## 🤝 Contributions

Les contributions sont ce qui fait de la communauté open source un endroit incroyable pour apprendre, s'inspirer et créer. Toute contribution est **grandement appréciée**.

Si vous avez une suggestion pour améliorer ce projet, n'hésitez pas à **forker le dépôt** et à proposer une pull request. Vous pouvez également ouvrir une issue avec le tag "enhancement".

N'oubliez pas de laisser une étoile ⭐ au projet ! Merci encore ! 🚀

### 🔧 Comment contribuer ?

1. **Forkez le projet**
2. **Créez une branche pour votre fonctionnalité**  
   Utilisez la commande suivante pour créer une nouvelle branche pour la fonctionnalité que vous souhaitez ajouter :
   ```bash
   git checkout -b fonctionnalité/IncroyableFonctionnalité
3. **Commitez vos modifications**
   Après avoir fait les modifications nécessaires, enregistrez-les avec un commit en utilisant la commande :
    ```bash
   git commit -m 'Ajout de la fonctionnalité IncroyableFonctionnalité'
4. **Poussez votre branche sur votre fork**
    Pour pousser vos changements sur votre fork, utilisez :
   ```bash
   git push origin fonctionnalité/IncroyableFonctionnalité
5. **Ouvrez une Pull Request**
    Une fois votre branche prête, ouvrez une pull request pour que vos modifications puissent être intégrées au projet principal.

### Top contributors:

<a href="https://github.com/JoachimLombardi/Projet_chef_d-oeuvre/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=JoachimLombardi/Projet_chef_d-oeuvre" alt="contrib.rocks image" />
</a>


<p align="right">(<a href="#readme-top">back to top</a>)</p>

## 📄 Licence

Distribué sous la licence du projet. Voir le fichier `LICENSE.txt` pour plus d'informations.


<p align="right">(<a href="#readme-top">back to top</a>)</p>



## 📬 Contact

Joachim Lombardi - [LinkedIn](https://www.linkedin.com/in/joachim-lombardi-machinelearning-intelligenceartificielle-datascientist/) - lombardi.joachim@gmail.com

Project Link: [https://github.com/JoachimLombardi/Projet_chef_d-oeuvre](https://github.com/JoachimLombardi/Projet_chef_d-oeuvre)


<p align="right">(<a href="#readme-top">back to top</a>)</p>



## 🏅 Badges du projet

![Contributors](https://img.shields.io/github/contributors/JoachimLombardi/Projet_chef_d-oeuvre.svg?style=for-the-badge)
![Forks](https://img.shields.io/github/forks/JoachimLombardi/Projet_chef_d-oeuvre.svg?style=for-the-badge)
![Stars](https://img.shields.io/github/stars/JoachimLombardi/Projet_chef_d-oeuvre.svg?style=for-the-badge)
![Issues](https://img.shields.io/github/issues/JoachimLombardi/Projet_chef_d-oeuvre.svg?style=for-the-badge)
![License](https://img.shields.io/github/license/JoachimLombardi/Projet_chef_d-oeuvre.svg?style=for-the-badge)

[Contributors](https://github.com/JoachimLombardi/Projet_chef_d-oeuvre/graphs/contributors)  
[Forks](https://github.com/JoachimLombardi/Projet_chef_d-oeuvre/network/members)  
[Stars](https://github.com/JoachimLombardi/Projet_chef_d-oeuvre/stargazers)  
[Issues](https://github.com/JoachimLombardi/Projet_chef_d-oeuvre/issues)  
[License](https://github.com/JoachimLombardi/Projet_chef_d-oeuvre/blob/master/LICENSE.txt)



