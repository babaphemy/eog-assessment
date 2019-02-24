import { takeEvery, call, put, cancel, all } from "redux-saga/effects";
import API from "../api";
import * as actions from "../actions";

// fetch 30 min drone and get last


function* watchFetchDrone() {
  const { error, data } = yield call(API.findDrone);
  if(error) {
    yield put({ type: actions.API_ERROR, code: error.code });
    yield cancel();
    return;
  }
  const position = data.data.pop() ;
  //console.log(position);
  yield put({ type: actions.DRONE_FETCHED, position});

}

function* watchDroneFetched(action) {
  const latitude = action.position.latitude;
  const longitude = action.position.longitude;
//  const { latitude, longitude } = action;
  const { error, data } = yield call(
    API.findLocationByLatLng,
    latitude,
    longitude
  );
  if (error) {
    console.log({ error });
    yield put({ type: actions.API_ERROR, code: error.code });
    yield cancel();
    return;
  }
  const location = data[0] ? data[0].woeid : false;
  if (!location) {
    yield put({ type: actions.API_ERROR });
    yield cancel();
    return;
  }
  yield put({ type: actions.WEATHER_ID_RECEIVED, id: location });

}

function* watchDroneAppLoad() {
  yield all([
    takeEvery(actions.FETCH_DRONE, watchFetchDrone),
    takeEvery(actions.DRONE_FETCHED, watchDroneFetched)
  ]);
}

export default [watchDroneAppLoad];
