FROM node:20-alpine

WORKDIR /app

# Install pnpm globally
RUN npm install -g pnpm@10.18.2

# Copy pnpm config first
COPY frontend/.npmrc ./

# Copy package files
COPY frontend/package.json frontend/pnpm-lock.yaml ./

# Install dependencies (frozen lockfile for production consistency)
RUN pnpm install --frozen-lockfile

# Copy source code
COPY frontend/ .

# Expose port
EXPOSE 5173

# Run dev server
CMD ["pnpm", "dev", "--host"]
