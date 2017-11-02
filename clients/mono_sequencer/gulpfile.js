var postcss = require('gulp-postcss');
var gulp = require('gulp');
var autoprefixer = require('autoprefixer');
var cssnano = require('cssnano');
var htmlmin = require('gulp-htmlmin');
var babel = require('gulp-babel');
var sass = require('gulp-sass');
var ts  = require('gulp-typescript');

require('gulp-watch');
require('babel-preset-es2015');


gulp.task('ts', function() {
  var tsResult = gulp.src("src/*.ts")
      .pipe(ts({
        noImplicitAny: true,
        out: "output.js"
      }));
  return tsResult.js.pipe(gulp.dest("dist"));
});

gulp.task('sass', function() {
  var plugins = [
    autoprefixer({
      browsers: ['last 5 versions']
    }),
    cssnano()
  ];
  return gulp.src('./src/*.scss')
    .pipe(sass().on('error', sass.logError))
    .pipe(postcss(plugins))
    .pipe(gulp.dest('./dist'));
});

gulp.task('js', function() {
  gulp.src(['./src/*.js', '!gulpfile.js'])
    .pipe(babel({
      presets: ['es2015']
    }))
    .pipe(gulp.dest('./dist'));
});

gulp.task('css', function() {
  var plugins = [
    autoprefixer({
      browsers: ['last 5 versions']
    }),
    cssnano()
  ];
  return gulp.src('./src/*.css')
    .pipe(postcss(plugins))
    .pipe(gulp.dest('./public'));
});

gulp.task('watch', function () {
  gulp.watch(['src/*'], ['build']);
});

gulp.task('build', ['sass', 'js', 'ts']);
