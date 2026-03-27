FROM node:22-alpine

WORKDIR /app

# Install dependencies first (cached layer)
COPY package.json package-lock.json* ./
RUN npm install

# Copy source code
COPY . .

EXPOSE 5177

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
