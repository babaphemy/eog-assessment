import React from "react";
import ReactDOM from "react-dom";
import Card from "@material-ui/core/Card";
import CardHeaderRaw from "@material-ui/core/CardHeader";
import CardContent from "@material-ui/core/CardContent";
import List from "@material-ui/core/List";
import ListItem from "@material-ui/core/ListItem";
import ListItemText from "@material-ui/core/ListItemText";
import AvatarRaw from "@material-ui/core/Avatar";
import { withStyles } from "@material-ui/core/styles";
import { compose, withProps } from "recompose";
import {
  withScriptjs,
  withGoogleMap,
  GoogleMap,
  Marker
} from "react-google-maps";

const cardStyles = theme => ({
  root: {
    background: theme.palette.primary.main
  },
  title: {
    color: "white"
  }
});
const CardHeader = withStyles(cardStyles)(CardHeaderRaw);

const styles = {
  card: {
    margin: "5% 25%"
  }
};
const avatarStyles = theme => ({
  root: {
    background: theme.palette.primary.main
  },
  title: {
    color: "white"
  }
});
const Avatar = withStyles(avatarStyles)(AvatarRaw);


const MapComponent = compose(
  withProps({
    /**
     * Note: create and replace your own key in the Google console.
     * https://console.developers.google.com/apis/dashboard
     * The key "AIzaSyBkNaAGLEVq0YLQMi-PYEMabFeREadYe1Q" can be ONLY used in this sandbox (no forked).
     */

    googleMapURL:
      "https://maps.googleapis.com/maps/api/js?key=AIzaSyC0tp5SMECT55RIixjFz19ehkfhoncV2pg&libraries=geometry,drawing,places",
    loadingElement: <div style={{ height: `100%` }} />,
    containerElement: <div style={{ height: `400px` }} />,
    mapElement: <div style={{ height: `100%` }} />
  }),
  withScriptjs,
  withGoogleMap
)(props => (
  <Card style = {{margin: "5% 25%"}}>
    <CardHeader title=  {props.title} />
    <CardContent>
    <GoogleMap defaultZoom={4} defaultCenter={{ lat:props.lati, lng:props.longi }}>
      {
        true && <Marker position={{ lat:props.lati, lng:props.longi }} />
      }

    </GoogleMap>
    <List>
      <ListItem>
        <Avatar>LO</Avatar>
        <ListItemText primary="Longitude" secondary={props.longi} />
      </ListItem>
      <ListItem>
        <Avatar>LA</Avatar>
        <ListItemText primary="Latitude" secondary={props.lati} />
      </ListItem>
      <ListItem>
        <Avatar>T</Avatar>
        <ListItemText primary="Temperature" secondary={props.temp} />
      </ListItem>
      </List>
    </CardContent>
  </Card>





));
export default MapComponent;
