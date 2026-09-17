# Sen Suivi — Front-end Angular
# Le projet Angular (package.json, angular.json, src/) sera initialisé à
# l'étape dédiée au front-end. Ce Dockerfile deviendra fonctionnel à ce moment-là.

FROM node:24-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 4200

CMD ["npm", "start", "--", "--host", "0.0.0.0"]
