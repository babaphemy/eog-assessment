import * as actions from "../actions";

const initialState = {
  loading: false,
  latitude: null,
  longitude:null
};
const droneLoading = (state, action) => {
  return { ...state, loading: true };
};

const droneFetched = (state, action) => {
  const latit = action.position.latitude;
  const longit = action.position.longitude;
  return { ...state,
     loading:false,
     latitude:latit,
     longitude:longit
   };
}


const handlers = {
  [actions.FETCH_DRONE]: droneLoading,
  [actions.DRONE_FETCHED]: droneFetched
};

export default (state = initialState, action) => {
  const handler = handlers[action.type];
  if (typeof handler === "undefined") return state;
  return handler(state, action);
};
