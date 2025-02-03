# Projet_chef_d'oeuvre

<!-- PROJECT LOGO -->
<br />
<div align="center">
<a href="https://media.licdn.com/dms/image/v2/D5612AQGgBoGZVp7XxA/article-cover_image-shrink_720_1280/article-cover_image-shrink_720_1280/0/1705242357114?e=1744243200&v=beta&t=68SvDGLDdBd0EIgvVtvfCbDXlYsybQBweopL5CnMtXs">
  <img src="https://media.licdn.com/dms/image/v2/D5612AQGgBoGZVp7XxA/article-cover_image-shrink_720_1280/article-cover_image-shrink_720_1280/0/1705242357114?e=1744243200&v=beta&t=68SvDGLDdBd0EIgvVtvfCbDXlYsybQBweopL5CnMtXs" alt="Logo" width="600" height="300">
</a>


<h3 align="center">RAG sur des résumés PubMed</h3>

  <p align="center">
    Cette application permet de poser des questions sur des résumés PubMed, elle permet également d'afficher la liste des articles avec les auteurs et affiliations correspondantes. Il est également possible de réaliser une évaluation de la qualité de la recherche et de la génération en faisant varié certains paramètres. </p>
</div>


<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>
</details>


<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Built With

* [![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
* [![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
* [![HTML](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)](https://developer.mozilla.org/en-US/docs/Web/HTML)
* [![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
* [![Elasticsearch](https://img.shields.io/badge/Elasticsearch-005571?style=for-the-badge&logo=elasticsearch&logoColor=white)](https://www.elastic.co/)
* [![Mistral AI](https://img.shields.io/badge/Mistral_AI-FF6F61?style=for-the-badge&logo=mistral&logoColor=white)](https://mistral.ai/)
* [![GPT](https://img.shields.io/badge/GPT-412991?style=for-the-badge&logo=openai&logoColor=white)](https://openai.com/)
* [![Grafana](https://img.shields.io/badge/Grafana-F46800?style=for-the-badge&logo=grafana&logoColor=white)](https://grafana.com/)
* [![Prometheus](https://img.shields.io/badge/Prometheus-E6522C?style=for-the-badge&logo=prometheus&logoColor=white)](https://prometheus.io/)
* [![Ollama](https://img.shields.io/badge/Ollama-000000?style=for-the-badge)](https://ollama.com/)
* [![Uptime Kuma](https://img.shields.io/badge/Uptime%20Kuma-0078D7?style=for-the-badge)](https://github.com/louislam/uptime-kuma)
* [![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)](https://developer.mozilla.org/fr/docs/Web/JavaScript)
* [![CSS](https://img.shields.io/badge/CSS-1572B6?style=for-the-badge&logo=css3&logoColor=white)](https://developer.mozilla.org/fr/docs/Web/CSS)
* [![Shell](https://img.shields.io/badge/Shell-4EAA25?style=for-the-badge&logo=gnu-bash&logoColor=white)](https://www.gnu.org/software/bash/)




<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- GETTING STARTED -->
## Getting Started

Vous avez besoin de [`docker`](https://www.docker.com/).

### Installation

1. Pour réaliser l'évaluation avec GPT4-o, vous avez besoin d'une [clé api](https://platform.openai.com/settings/organization/api-keys).
2. Cloner le repo
   ```sh
   git clone https://github.com/github_username/repo_name.git](https://github.com/JoachimLombardi/Projet_chef_d-oeuvre.git
   ```
3. Avant de lancer l'application, assurez-vous que vous avez configuré les variables d'environnement nécessaires.
   Créer un fichier .env dans le dossier `pubmed_analyze/docker` sur le modèle suivant:
```env
# Base de données PostgreSQL
DATABASE_NAME=your_database_name_here  # Remplacez par le nom de votre base de données
DATABASE_USER=your_database_user_here  # Remplacez par votre nom d'utilisateur de base de données
DATABASE_PASSWORD=your_database_password_here  # Remplacez par le mot de passe de votre base de données
DATABASE_HOST=your_database_host_here  # Remplacez par l'hôte de votre base de données (par exemple 'localhost' ou l'IP de votre serveur)
DATABASE_PORT=5432  # Laissez tel quel si vous utilisez le port par défaut de PostgreSQL

# Clés API externes
OPENAI_API_KEY=your_openai_api_key_here  # Remplacez par votre clé API OpenAI
HUGGING_FACE_HUB_TOKEN=your_hugging_face_token_here  # Remplacez par votre jeton Hugging Face

# Configuration de l'email
EMAIL_HOST_USER=your_email_address_here  # Remplacez par l'adresse email utilisée pour envoyer les emails via Django
EMAIL_HOST_PASSWORD=your_email_password_here  # Remplacez par le mot de passe de votre adresse email

# Paramètres de Django
SECRET_KEY=your_django_secret_key_here  # Remplacez par une clé secrète unique pour votre projet Django
DEBUG=True  # Laissez à True pour le développement, passez à False pour la production
ALLOWED_HOSTS=localhost,127.0.0.1,django  # Laissez tel quel ou ajoutez d'autres hôtes autorisés

# URL de connexion à la base de données (si utilisée)
DATABASE_URL=postgres://your_database_user_here:your_database_password_here@your_database_host_here:5432/your_database_name_here  # Remplacez par l'URL de connexion à votre base de données PostgreSQL

4. Lancer le client Docker

5. Dans le terminal tapez:
   ```sh
   docker-compose --env-file .env up --build
   ```
6. Dans un navigateur, tapez l'URL suivante pour accéder à l'application:
   http://localhost:8000/article/read/

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- USAGE EXAMPLES -->
## Usage
Poser n'importe quelle question au RAG telles que: 
* What were the key findings of the qualitative study exploring patients' experiences and understanding of Multiple Sclerosis (MS)?
* What were the findings regarding newly appearing lesions in Multiple Sclerosis (MS) and their evolution into slowly expanding lesions (SELs) in the context of fingolimod 
  treatment?
* How can artificial intelligence (AI) and machine learning (ML) improve the diagnosis and prediction of Multiple Sclerosis (MS), and what challenges are associated 
  with their implementation ?
Il va retourner une réponse dans un cadre ainsi que la liste des trois premiers articles utilisés pour la réponse dans le cadre suivant.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- ROADMAP -->
## Roadmap

- [ ] Feature 1
- [ ] Feature 2
- [ ] Feature 3
    - [ ] Nested Feature

See the [open issues](https://github.com/github_username/repo_name/issues) for a full list of proposed features (and known issues).

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTRIBUTING -->
## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Top contributors:

<a href="https://github.com/github_username/repo_name/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=github_username/repo_name" alt="contrib.rocks image" />
</a>



<!-- LICENSE -->
## License

Distributed under the project_license. See `LICENSE.txt` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTACT -->
## Contact

Your Name - [@twitter_handle](https://twitter.com/twitter_handle) - email@email_client.com

Project Link: [https://github.com/github_username/repo_name](https://github.com/github_username/repo_name)

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- ACKNOWLEDGMENTS -->
## Acknowledgments

* []()
* []()
* []()

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[contributors-shield]: https://img.shields.io/github/contributors/github_username/repo_name.svg?style=for-the-badge
[contributors-url]: https://github.com/github_username/repo_name/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/github_username/repo_name.svg?style=for-the-badge
[forks-url]: https://github.com/github_username/repo_name/network/members
[stars-shield]: https://img.shields.io/github/stars/github_username/repo_name.svg?style=for-the-badge
[stars-url]: https://github.com/github_username/repo_name/stargazers
[issues-shield]: https://img.shields.io/github/issues/github_username/repo_name.svg?style=for-the-badge
[issues-url]: https://github.com/github_username/repo_name/issues
[license-shield]: https://img.shields.io/github/license/github_username/repo_name.svg?style=for-the-badge
[license-url]: https://github.com/github_username/repo_name/blob/master/LICENSE.txt
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://linkedin.com/in/linkedin_username
[product-screenshot]: images/screenshot.png
[Next.js]: https://img.shields.io/badge/next.js-000000?style=for-the-badge&logo=nextdotjs&logoColor=white
[Next-url]: https://nextjs.org/
[React.js]: https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB
[React-url]: https://reactjs.org/
[Vue.js]: https://img.shields.io/badge/Vue.js-35495E?style=for-the-badge&logo=vuedotjs&logoColor=4FC08D
[Vue-url]: https://vuejs.org/
[Angular.io]: https://img.shields.io/badge/Angular-DD0031?style=for-the-badge&logo=angular&logoColor=white
[Angular-url]: https://angular.io/
[Svelte.dev]: https://img.shields.io/badge/Svelte-4A4A55?style=for-the-badge&logo=svelte&logoColor=FF3E00
[Svelte-url]: https://svelte.dev/
[Laravel.com]: https://img.shields.io/badge/Laravel-FF2D20?style=for-the-badge&logo=laravel&logoColor=white
[Laravel-url]: https://laravel.com
[Bootstrap.com]: https://img.shields.io/badge/Bootstrap-563D7C?style=for-the-badge&logo=bootstrap&logoColor=white
[Bootstrap-url]: https://getbootstrap.com
[JQuery.com]: https://img.shields.io/badge/jQuery-0769AD?style=for-the-badge&logo=jquery&logoColor=white
[JQuery-url]: https://jquery.com 

