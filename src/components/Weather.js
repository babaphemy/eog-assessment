import React, { Component } from "react";
import { connect } from "react-redux";
import * as actions from "../store/actions";
import LinearProgress from "@material-ui/core/LinearProgress";
import ChipRaw from "@material-ui/core/Chip";
import { withStyles } from "@material-ui/core/styles";
import Dash from '../components/ui/dash';

const cardStyles = theme => ({
  root: {
    background: theme.palette.secondary.main
  },
  label: {
    color: theme.palette.primary.main
  }
});
const Chip = withStyles(cardStyles)(ChipRaw);

class Weather extends Component {
  componentDidMount() {
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
      latitude,
      longitude,
      temperatureinFahrenheit
    } = this.props;
    if (loading) return <LinearProgress />;
    return (
      <div>
      <Dash
        title={`Weather in ${name}: ${weather_state_name} `}
        temp={this.props.temperatureinFahrenheit}
        lat={`${latitude} `}
        long={this.props.longitude}
        lastr={'3 seconds'}
      />
      </div>
    );
  }
}

const mapState = (state, ownProps) => {
  const {
    loading,
    name,
    weather_state_name,
    latitude,
    longitude,
    temperatureinFahrenheit
  } = state.weather;
  return {
    loading,
    name,
    weather_state_name,
    latitude,
    longitude,
    temperatureinFahrenheit
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
  mapState,
  mapDispatch
)(Weather);
