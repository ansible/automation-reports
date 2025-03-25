import { configureStore } from '@reduxjs/toolkit';
import filterSlice from '@app/Store/filterSlice';
import { thunk } from 'redux-thunk';
import commonSlice from '@app/Store/commonSlice';

const reducer = {
  filters: filterSlice,
  common: commonSlice,
};

export const store = configureStore({
  reducer,
  middleware: (getDefaultMiddleware) => getDefaultMiddleware().prepend(thunk),
});
export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

export type AppStore = typeof store;
