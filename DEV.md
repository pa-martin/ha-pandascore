# Actions automatique

Des hooks Git doivent être installés avant de commit des modifications. Ces hooks s'installent avec la commande :

```shell
pre-commit install --hook-type pre-commit --hook-type commit-msg
```

# Créer une instance HA via Docker

L'objectif ici est de créer un container Docker d'Home Assistant vierge avec uniquement l'intégration
en cours de développement. Cela permet de tester l'intégration dans un environnement propre, sans interférence d'autres intégrations ou configurations.

## Container Docker

Voici un exemple de `docker-compose.yml` pour créer une instance HA avec uniquement l'intégration en cours de développement :

```yaml
services:
  homeassistant:
    container_name: "homeassistant"
    image: "homeassistant/home-assistant:stable"
    volumes:
      - "./config:/config"
      - "/etc/localtime:/etc/localtime:ro"
      - "./custom_components:/config/custom_components"
    restart: unless-stopped
    privileged: true
    ports:
      - "80:8123"
      - "443:8123"
    environment:
      TZ: Europe/Paris
```

Ou via la ligne de commande :

```bash
docker run -d \
    --name homeassistant \
    --privileged \
    --restart=unless-stopped \
    -p 80:8123 \
    -p 443:8123 \
    -e TZ=Europe/Paris \
    -v ./build:/config \
    -v /etc/localtime:/etc/localtime:ro \
    -v ./custom_components:/config/custom_components \
    --network=host \
    ghcr.io/home-assistant/home-assistant:stable
```
