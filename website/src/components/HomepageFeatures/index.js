import React from 'react';
import clsx from 'clsx';
import styles from './styles.module.css';

const FeatureList = [
  {
    title: 'Easy to Use',
    Svg: require('@site/static/img/undraw_scooter_re_lrsb.svg').default,
    description: (
      <>
        TRAC is designed to be easy to use. If you have a working <code>main.py</code>
        on your local machine, you can deploy it as an interactive web app in a few
        lines of configurations.
      </>
    ),
  },
  {
    title: 'Focus on What Matters',
    Svg: require('@site/static/img/undraw_dev_focus_re_6iwt.svg').default,
    description: (
      <>
        TRAC lets you focus on your solution, not on the UI, infrastructure, and other details.
        Just develop your Data Science solution. We will take care of the rest.
      </>
    ),
  },
  {
    title: 'From local to remote',
    Svg: require('@site/static/img/undraw_server_cluster_jwwq.svg').default,
    description: (
      <>
        If you code can run locally, then it can run remotely.
        We help to scale your solution. Need to conduct 1000 what-if experiments? No problem.
      </>
    ),
  },
];

function Feature({Svg, title, description}) {
  return (
    <div className={clsx('col col--4')}>
      <div className="text--center">
        <Svg className={styles.featureSvg} role="img" />
      </div>
      <div className="text--center padding-horiz--md">
        <h3>{title}</h3>
        <p>{description}</p>
      </div>
    </div>
  );
}

export default function HomepageFeatures() {
  return (
    <section className={styles.features}>
      <div className="container">
        <div className="row">
          {FeatureList.map((props, idx) => (
            <Feature key={idx} {...props} />
          ))}
        </div>
      </div>
    </section>
  );
}
