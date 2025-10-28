# OntarioDoctor Frontend

Vue 3 + TypeScript chat interface for the OntarioDoctor medical symptom-checker.

## Tech Stack

- **Framework**: Vue 3 (Composition API)
- **State Management**: Pinia
- **Styling**: TailwindCSS + shadcn-vue
- **Language**: TypeScript
- **Build Tool**: Vite

## Features

- 💬 Session-based chat interface
- 🔴 Red-flag alerts for emergencies
- 📚 Citation display with source links
- 🎨 Responsive design with TailwindCSS
- ⚡ Real-time message updates
- 🇨🇦 Ontario-specific medical resources

## Setup

### 1. Install Dependencies

```bash
pnpm install
```

### 2. Configure Environment

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Edit `.env` if needed (default points to `http://localhost:8000`):

```
VITE_API_URL=http://localhost:8000
```

### 3. Run Development Server

```bash
pnpm dev
```

The app will be available at `http://localhost:5173`

## Build for Production

```bash
pnpm build
```

Built files will be in `dist/`

## Project Structure

```
src/
├── api/              # API client
│   └── client.ts
├── components/       # Vue components
│   ├── ChatInterface.vue
│   ├── MessageBubble.vue
│   ├── CitationCard.vue
│   ├── RedFlagAlert.vue
│   └── InputBox.vue
├── stores/           # Pinia stores
│   └── chatStore.ts
├── types/            # TypeScript types
│   └── chat.ts
├── views/            # Page views
│   └── ChatView.vue
├── App.vue           # Root component
└── main.ts           # Entry point
```

## Usage

1. **Start chatting**: Type your symptoms in the input box
2. **View citations**: References appear below assistant messages
3. **Red flags**: Emergency alerts appear at the top if detected
4. **Clear history**: Use the "Clear History" button to start fresh

## Ontario Resources

The app provides Ontario-specific medical resources:

- **Telehealth Ontario**: 1-866-797-0000 (24/7)
- **Emergency**: 911
- **Non-urgent**: Family doctor or walk-in clinic

## Development

### Type Checking

```bash
pnpm type-check
```

### Format Code

```bash
pnpm format
```

### Run Tests

```bash
pnpm test:unit
```

## Environment Variables

- `VITE_API_URL`: Backend API Gateway URL (default: `http://localhost:8000`)

## Recommended IDE Setup

[VS Code](https://code.visualstudio.com/) + [Vue (Official)](https://marketplace.visualstudio.com/items?itemName=Vue.volar)

## Notes

- This is a symptom-checker tool, **not a replacement for professional medical advice**
- All responses are grounded in medical sources with citations
- Red-flag detection routes urgent cases to emergency services
- Session-based only (no user accounts or data persistence)
