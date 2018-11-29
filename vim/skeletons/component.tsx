import * as React from 'react';
import * as ReactDOM from 'react-dom';

import './__NAME__.scss';

interface Props {
}

export function __NAME__(props: Props) {
  return (
    <div>
      Hello from __NAME__
    </div>
  );
};

interface State {
}

export class __NAME__ extends React.Component<Props, State> {
  state: State = {
  };

  updateSomeState() {
    const changes = {
    };
    this.setState(Object.assign({}, this.state, changes));
  }

  render() {
    return (
      <div>
        Hello from __NAME__
      </div>
    );
  }
}
