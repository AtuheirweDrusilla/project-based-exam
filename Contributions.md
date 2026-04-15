
Ogwang Andrew (M23B23/050) Backend Foundation (Person 1):
• Corrected database migration schema mismatches.
• Populated database using TMDB data sync commands.
• Fixed application naming and missing CORS middleware in settings.
• Corrected HTTP methods (POST to GET) for movie search and trending endpoints.

Atuheirwe Drusilla (S24B23/106) Frontend Foundation (Person 2):
• Implemented missing TypeScript definitions for WatchlistItem.
• Resolved prop mismatches on the Home page to fix broken movie carousels.
• Added global keyboard shortcut (⌘K / Ctrl+K) for the search interface.

Asingwire Arnold (S24B23/013) Code Quality Part 1 (Person 3):
• Eliminated dead and duplicated code (e.g., compare_two_movies).
• Improved readability by replacing single-letter variables with descriptive names.
• Extracted the _serialize_tmdb_results helper to follow DRY principles.
• Optimized logic by replacing long if/elif chains with dictionary lookups.

Akampurira Aisha (S24B23/081) Code Quality Part 2 (Person 4):
• Replaced hardcoded TMDB image URLs with dynamic settings variables.
• Optimized loops by moving static maps (PROVIDER_TYPE_MAP) to module level.
• Standardized documentation and section headers across the codebase.
• Added comprehensive docstrings to all public API views and ViewSets.

Kobumanzi Trishia (M24B23/011) Backend Testing (Person 5):
• Developed 35 backend unit tests across 10 test classes.
• Verified movie model properties, including URL builders and string representations.
• Tested API endpoints for Search, Mood, and Comparison for proper error handling.
• Validated TMDB serializers to ensure accurate data transformation.

Aijuka Jonah (S24B23/097) Frontend Testing (Person 6):
• Created 20 frontend unit tests for data display utility functions.
• Configured Jest and ts-jest for the TypeScript testing environment.
• Conducted risk analysis for untested frontend areas.

Katende Derrick Elvan (S23B23/024) Movie Detail Page (Person 7):
• Repaired broken recommendation fetch logic on the movie details page.
• Fixed the "Because You Liked" personalized fetch feature.

Kasule Ezra Evans (S24B23/036) Smart Collections Backend (Person 8):
• Engineered models and serializers for the Smart Collections feature.
• Developed the backend views and URL routing for collection management.

Opifudrira Timothy (S23B23/086) Smart Collections Frontend (Person 9):
• Developed the API client and TypeScript types for Smart Collections.
• Built four UI pages for collections and integrated them into the navigation.
• Fixed pagination and navigation issues within the collection views.

Mutumba Benjamin Mubeezi (S23B23/010) Interaction Persistence (Person 10):
• Wired frontend interaction handlers (Like/Dislike/Bookmark) to the backend API.
• Ensured state persistence for user interactions across the application.
