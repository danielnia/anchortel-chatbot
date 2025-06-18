FROM node:18-alpine

RUN npm install -g http-server

WORKDIR /app

COPY public/ .

EXPOSE 8080

CMD ["http-server", ".", "-p", "8080", "-a", "0.0.0.0"]
