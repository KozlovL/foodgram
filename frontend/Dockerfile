# build env
FROM node:21.7.1-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . ./
RUN npm run build
RUN mkdir -p /frontend_static && \
    cp -r build/. /frontend_static/ && \
    cp -r build/static/. /frontend_static/
