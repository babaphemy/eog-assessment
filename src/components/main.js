import React from 'react';
import { Switch, Route } from 'react-router-dom';

import Home from '../components/NowWhat';
import Chartview from '../components/ui/chart';
import Dashview from './Weather';

const Main = () => (
  <main>
    <Switch>
      <Route exact path='/' component={Home} />
      <Route path='/dashboard' component={Dashview} />
      <Route path='/chart' component={Chartview} />
    </Switch>
  </main>
)

export default Main;
