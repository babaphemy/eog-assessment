import React from 'react';
import Card from "@material-ui/core/Card";
import CardHeaderRaw from "@material-ui/core/CardHeader";
import CardContent from "@material-ui/core/CardContent";
import List from "@material-ui/core/List";
import ListItem from "@material-ui/core/ListItem";
import ListItemText from "@material-ui/core/ListItemText";
import { withStyles } from "@material-ui/core/styles";
import AvatarRaw from "@material-ui/core/Avatar";

const cardStyles = theme => ({
  root: {
    background: theme.palette.primary.main
  },
  title: {
    color: "white"
  }
});
const CardHeader = withStyles(cardStyles)(CardHeaderRaw);

const avatarStyles = theme => ({
  root: {
    background: theme.palette.primary.main
  },
  title: {
    color: "white"
  }
});
const Avatar = withStyles(avatarStyles)(AvatarRaw);

const styles = {
  card: {
    margin: "5% 25%"
  }
};

const Dashview = props => {
  const { classes } = props;
  return (
    <Card className={classes.card}>
      <CardHeader title=  {props.title} />
      <CardContent>
        <List>
          <ListItem>
            <Avatar className={classes.avatar}>T</Avatar>
            <ListItemText primary="Temperature" secondary={props.temp} />
          </ListItem>
          <ListItem>
            <Avatar className={classes.orangeAvatar}>LA</Avatar>
            <ListItemText primary="Latitude" secondary={props.lat} />


          </ListItem>
          <ListItem>
            <Avatar className={classes.blueAvatar}>LO</Avatar>
            <ListItemText primary="Longitude" secondary={props.long} />
          </ListItem>
          <ListItem>
            <Avatar className={classes.avatar}>I</Avatar>
            <ListItemText primary="Last Received" secondary={props.lastr} />
          </ListItem>
        </List>
      </CardContent>
    </Card>
  );

}



export default withStyles(styles)(Dashview);
