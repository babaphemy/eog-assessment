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
      temperatureinFahrenheit
    } = this.props.wthr;
    const latitude = this.props.drn.latitude;
    const longitude = this.props.drn.longitude;
    if (loading) return <LinearProgress />;
    return (
      <div>
      <Dash
        title={`Weather in ${name}: ${weather_state_name} `}
        temp={`${temperatureinFahrenheit} `}
        lat={`${latitude} `}
        long={`${longitude} `}
        lastr={'3 seconds'}
      />
      </div>
    );
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
)(Weather);
