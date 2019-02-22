import React from "react";
import Typography from "@material-ui/core/Typography";
import AppBar from "@material-ui/core/AppBar";
import Toolbar from "@material-ui/core/Toolbar";
import { Link } from "react-router-dom";
import { withStyles } from "@material-ui/core/styles";

const styles = {
  grow: {
    flexGrow: 1
  }
};

const Header = props => {
  const { classes } = props;

  const name = "femi's";
  return (
    <AppBar position="static">
      <Toolbar>
        <Typography variant="h6" color="inherit" className={classes.grow}>
          <Link to="/" style={{ textDecoration: 'none', color: 'white' }}>{name} EOG React Visualization Assessment</Link>
        </Typography>
      </Toolbar>
    </AppBar>
  );
};

export default withStyles(styles)(Header);
