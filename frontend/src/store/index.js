/**
 * Redux Store Configuration
 */

import { configureStore } from '@reduxjs/toolkit';
import carbonReducer from '../features/carbon/store/carbonSlice';

export const store = configureStore({
  reducer: {
    carbon: carbonReducer
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: false
    })
});

export default store;
