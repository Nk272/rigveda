# Rigveda Explorer

An interactive visualization of Rigveda hymns with beautiful bubble animations.

## Features

- 🫧 Floating bubble visualization (size = hymn score)
- 🔴 Red dots on white background
- 🎯 Biggest hymn in center
- ✨ Click bubbles to explore deities and similar hymns
- 🔄 Navigate between similar hymns seamlessly

## Getting Started

```bash
# Install dependencies
npm install

# Run development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to see the app.

## Tech Stack

- **Framework:** Next.js 14 (App Router)
- **Styling:** Tailwind CSS
- **Animation:** Framer Motion
- **Database:** SQLite (better-sqlite3)
- **Language:** TypeScript

## Project Structure

```
rigveda-explorer/
├── app/
│   ├── api/          # API routes for hymn data
│   ├── page.tsx      # Main page
│   └── layout.tsx    # Layout wrapper
├── components/
│   └── HymnBubbles.tsx  # Main visualization component
├── lib/
│   └── db.ts         # Database utilities
├── types/
│   └── hymn.ts       # TypeScript interfaces
└── hymn_vectors.db   # SQLite database
```

## How It Works

1. **Bubbles:** Each hymn is a floating bubble, size based on score
2. **Click:** Opens detail view with orbiting deities
3. **Similar Hymns:** Shows 8 most similar hymns around the detail
4. **Navigate:** Click any similar hymn to explore further

## Database

The app uses a pre-generated SQLite database containing:
- 1028 Rigveda hymns
- 89-dimension deity vectors
- Hymn scores based on deity frequencies
- Similarity calculations

## Development

```bash
# Run in development mode
npm run dev

# Build for production
npm run build

# Start production server
npm start
```
