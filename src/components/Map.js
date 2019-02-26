import React, { Component } from "react";
import { connect } from "react-redux";
import * as actions from "../store/actions";
import MapComponent from '../components/ui/chart';
import { withStyles } from "@material-ui/core/styles";
import LinearProgress from "@material-ui/core/LinearProgress";
class Map extends Component {

  state = {
  isMarkerShown: false,
  longitude:-95.3698,
  latitude:29.7604
  }
  delayedShowMarker = () => {
  setTimeout(() => {

    this.setState({ isMarkerShown: true });
  }, 2000)
  }


  componentDidMount() {
    this.delayedShowMarker();
    this.intervalId = setInterval(() => this.props.onLoad(), 4000);
    this.props.onLoad();
  }


  componentWillUnmount() {
    clearInterval(this.intervalId);
  }




  render() {
    const {
      loading,
      name,
      weather_state_name,
      temperatureinFahrenheit
    } = this.props.wthr;

    if (loading) return <LinearProgress />;
    return (
      <MapComponent
        title={`Weather in ${name}: ${weather_state_name} `}
        temp={`${temperatureinFahrenheit} `}
        lati= {this.props.drn.latitude || 29.7604}
        longi={this.props.drn.longitude || -95.3698}
        isMarkerShown={this.state.isMarkerShown}
      />
    )
  }
}

const mapStateToProps = state => {
  return {
    wthr: state.weather,
    drn: state.drone
  };
};

const mapDispatch = dispatch => ({
  onLoad: () =>
    dispatch({
      type: actions.FETCH_DRONE,
      //type: actions.FETCH_WEATHER,
      //longitude: -95.3698,
      //latitude: 29.7604
    })
});

export default connect(
  mapStateToProps,
  mapDispatch
)(Map);
