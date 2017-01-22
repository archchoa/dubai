var webpack = require('webpack');
var path = require('path');

var BUILD_DIR = path.resolve(__dirname, 'client/src/build');
var APP_DIR = path.resolve(__dirname, 'client/src/app');

var defaultPort = 3000;
var serverPort = 8080;

var config = {
  port: defaultPort,
  entry: {
  	app: [
      'webpack-dev-server/client?http://localhost:' + defaultPort,
      'webpack-hot-middleware/client',
  	  APP_DIR + '/index.js',
  	  APP_DIR + '/index.html',
	]
  },
  output: {
    path: BUILD_DIR,
    filename: 'bundle.js',
    publicPath: '/public',
  },
  devServer: {
  	contentBase: './client/src/build',
    historyApiFallback: true,
    inline: true,
    port: defaultPort,
    publicPath: '/public/',
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:' + serverPort,
        secure: false
      }
    },
    stats: {
    	progress: true,
    	colors: true
    }
  },
  module: {
    loaders: [
      {
        test: /\.js?/,
        include: APP_DIR,
        exclude: '/node_modules/',
        loaders: ['react-hot', 'babel-loader']
      },
      {
		test: /\.html$/,
		loader: "file?name=[name].[ext]",
	  },
    ],
  },
  plugins: [
	new webpack.HotModuleReplacementPlugin(),
  ],
};

module.exports = config;