import { configureStore } from '@reduxjs/toolkit';
import filterSlice from '@app/Store/filterSlice';
import reportSlice  from '@app/Store/reportSlice';
import reportDetailsSlice from '@app/Store/reportDetailsSlice';
import { thunk } from 'redux-thunk';

const reducer = {
  filters: filterSlice,
  reports: reportSlice,
  reportDetails: reportDetailsSlice,
}

export const store = configureStore({
  reducer,
  middleware: (getDefaultMiddleware) => getDefaultMiddleware().prepend(thunk),
});
export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

export type AppStore = typeof store;
