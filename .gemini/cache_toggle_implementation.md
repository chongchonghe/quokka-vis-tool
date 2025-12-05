# Cache Toggle Feature Implementation

## Summary
Added a new feature to toggle caching on/off in the web application. This allows users to control whether plot generation results are cached for better performance or regenerated fresh each time.

## Changes Made

### Frontend Changes

#### 1. App.jsx
- Added `useCache` state variable (default: `true`)
- Passed `useCache` to both Controls and Viewer components
- The cache setting is applied immediately (no need to click Refresh)

#### 2. Controls.jsx
- Added `useCache` prop to component parameters
- Added a checkbox control labeled "Use Cache" in the 3D rendering section
- Positioned after the "Show Box Frame" checkbox for logical grouping

#### 3. Viewer.jsx
- Added `useCache` prop to component parameters
- Included `useCache` in the dependency array for useEffect
- Passed `use_cache` parameter to the backend API in the fetch URL

### Backend Changes

#### 4. main.py
- **Refactored caching mechanism** to support conditional caching:
  - Renamed original `_generate_plot_image` to `_generate_plot_image_impl` (core implementation without caching)
  - Created `_generate_plot_image_cached` with `@lru_cache` decorator (cached version)
  - Created new `_generate_plot_image` router function that:
    - Accepts `use_cache` parameter (default: `True`)
    - Routes to cached version when `use_cache=True`
    - Routes to non-cached version when `use_cache=False`
  
- **Updated API endpoints**:
  - `/api/slice`: Added `use_cache` parameter (default: `True`)
  - `/api/export/current_frame`: Added `use_cache` parameter (default: `True`)
  - `/api/export/animation`: Uses `use_cache=True` for better performance

## How It Works

1. **User toggles the "Use Cache" checkbox** in the UI
2. **Frontend immediately updates** the `useCache` state
3. **Viewer component re-fetches** the image with the new `use_cache` parameter
4. **Backend routes the request**:
   - If `use_cache=True`: Uses the cached version (faster, reuses previously generated plots)
   - If `use_cache=False`: Generates a fresh plot every time (slower, but ensures latest data)

## Benefits

- **Performance**: Caching enabled by default provides fast response times
- **Flexibility**: Users can disable cache when they need fresh data or are debugging
- **Transparency**: Clear UI control makes it obvious when caching is active
- **Export optimization**: Animation exports always use cache for better performance

## Default Behavior

- Cache is **enabled by default** (`useCache = true`)
- This maintains the existing performance characteristics
- Users can disable it when needed for specific use cases
