import { configureStore } from '@reduxjs/toolkit';

const reducer = (state = {}) => state

export const store = configureStore({
  reducer,
  middleware: (getDefaultMiddleware) => getDefaultMiddleware(),
});
export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

export type AppStore = typeof store;
