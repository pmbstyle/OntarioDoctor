FROM node:20-alpine

WORKDIR /app

# Install pnpm globally
RUN npm install -g pnpm@10.18.2

# Copy pnpm config first
COPY frontend/.npmrc ./

# Copy package files
COPY frontend/package.json ./

# Install dependencies (will generate new lockfile)
RUN pnpm install

# Copy source code
COPY frontend/ .

# Expose port
EXPOSE 5173

# Run dev server
CMD ["pnpm", "dev", "--host"]
