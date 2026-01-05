FROM node:22-alpine AS build

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build the app
RUN npm run build -- --configuration production

# Debug: List what was built
RUN ls -la /app/dist/

# Stage 2: Serve with Nginx
FROM nginx:alpine

# Copy built app - Angular 18 uses this path
COPY --from=build /app/dist/advance-company-frontend/browser /usr/share/nginx/html

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]