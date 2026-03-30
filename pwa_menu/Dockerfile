FROM node:22-alpine

WORKDIR /app

# Install dependencies first (cached layer)
COPY package.json ./
RUN npm install --legacy-peer-deps

# Copy source code
COPY . .

EXPOSE 5176

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
