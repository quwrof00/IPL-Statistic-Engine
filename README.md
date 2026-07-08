# IPL Rating System & Apex Engine

This project contains a comprehensive data analytics pipeline and a modern, high-performance dashboard to evaluate IPL players. It is built using a custom algorithm called the **Apex Engine** (V11 and V14) that evaluates and contextualizes player performances across seasons using raw metrics, advanced analytics, Z-scores, playoff impacts, and more.

## Project Structure

This project has two main parts:
1. **Python Data Pipeline (`/`)**: Processes CSV files (match-by-match data) to generate aggregated player statistics, run complex analytical models (including Z-score generation, PCA logic, etc.), and outputs structured JSON data.
2. **Next.js Dashboard (`/ipl`)**: A visually stunning, highly interactive web application built with React, Next.js, and Recharts to visualize the analyzed data via tables, radar charts, and scatter plots.

---

## 1. Data Pipeline

The root directory contains all the python scripts necessary to parse, process, and rate players.

### Core Scripts
- **`build_final_score.py` / `build_v14_score.py`**: The core rating engines that read aggregated data and produce the final `Apex V11` and `Apex V14` rating scores along with sub-metrics (Percentiles, Z-scores, base metrics, impact multipliers). 
- **`analyze_allrounders.py` / `analyze_phases.py`**: Scripts dedicated to producing domain-specific analytics for all-rounders and match phases (powerplay, death overs).
- **`aggregate_match_stats.py`**: Aggregates the raw CSV deliveries and matches data into season-by-season player formats.

The pipeline writes the final output to `ipl/public/data.json`, which is then seamlessly consumed by the web dashboard.

---

## 2. Web Dashboard

The `ipl` directory contains a Next.js application that visualizes the results of the Apex Engine. It features:
- A beautiful, premium dark mode aesthetic with copper accents.
- A **Leaderboard Table** with comprehensive sorting by advanced metrics.
- A **Comparison Modal** utilizing Radar Charts to stack players head-to-head.
- An **Advanced Scatter Plot** that lets you correlate any two sub-metrics (e.g., Strike Rate Z-Score vs. Economy Z-Score, Base Batting vs. Playoff Impact).

### Running the App Locally

1. Navigate to the `ipl` directory:
   ```bash
   cd ipl
   ```
2. Install the necessary dependencies (if you haven't already):
   ```bash
   npm install
   ```
3. Start the development server:
   ```bash
   npm run dev
   ```
4. Open [http://localhost:3000](http://localhost:3000) in your browser to view the dashboard.

### Building for Production

To create an optimized production build, run:
```bash
npm run build
```
You can then start the production server with:
```bash
npm start
```

## Deployment

Because this project uses Next.js, the easiest way to deploy it to the world is via [Vercel](https://vercel.com/) or [Netlify](https://www.netlify.com/).

1. Initialize a git repository and commit your code:
   ```bash
   git init
   git add .
   git commit -m "Initial commit - IPL Rating System complete"
   ```
2. Push to GitHub, GitLab, or Bitbucket.
3. Import your repository to Vercel or Netlify. The deployment platform will automatically detect Next.js and handle the build process, taking your dashboard live instantly!
