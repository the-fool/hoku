var postcss = require('gulp-postcss');
var gulp = require('gulp');
var autoprefixer = require('autoprefixer');
var cssnano = require('cssnano');
var htmlmin = require('gulp-htmlmin');
var babel = require('gulp-babel');
var sass = require('gulp-sass');
require('gulp-watch');
require('babel-preset-es2015');


gulp.task('sass', function() {
  var plugins = [
    autoprefixer({
      browsers: ['last 5 versions']
    }),
    cssnano()
  ];
  return gulp.src('./src/**/*.scss')
    .pipe(sass().on('error', sass.logError))
    .pipe(postcss(plugins))
    .pipe(gulp.dest('./public'));
});

gulp.task('js', function() {
  gulp.src(['./src/**/*.js'])
    .pipe(babel({
      presets: ['es2015']
    }))
    .pipe(gulp.dest('./public'));
});

gulp.task('watch', function() {
  gulp.watch(['./src/**/*'], ['build']);
});

gulp.task('build', ['sass', 'js']);
