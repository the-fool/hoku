module Main exposing (..)

import Html exposing (Html, program, div)
import Html.Events exposing (onClick)
import DynamicStyle exposing (hover, hover_)
import Svg exposing (circle, line, svg, g, rect)
import Svg.Attributes exposing (..)
import Time exposing (Time, second, millisecond)
import List.Extra exposing ((!!))


main =
    program { init = init, view = view, update = update, subscriptions = subs }


type Color
    = Red
    | Blue
    | Green
    | Yellow
    | White


type alias NoteBank =
    { color : Color
    , notes : Note
    }


type alias Note =
    { do : Bool
    , re : Bool
    , mi : Bool
    , fa : Bool
    , sol : Bool
    , la : Bool
    , ti : Bool
    , do2 : Bool
    }


initNotes : Note
initNotes =
    { do = False
    , re = False
    , mi = False
    , fa = False
    , sol = False
    , la = False
    , ti = False
    , do2 = False
    }



-- MODEL


type alias Model =
    { step : Int
    , noteBanks : List NoteBank
    }



-- VIEW


steps : Int
steps =
    16


view : Model -> Html Msg
view model =
    let
        angle =
            turns <| toFloat model.step / toFloat steps

        handX =
            toString (10 + 9 * cos (angle))

        handY =
            toString (10 + 9 * sin (angle))
    in
        svg [ viewBox "0 0 200 100", width "1600px", height "800px" ]
            [ rect [ x "0", y "0", width "200", height "100" ] []
            , g [ transform "translate(20, 0)", id "note-banks" ] (noteBanks model)
            , circle [ cx "10", cy "10", r "9", fill "#0B79CE" ] []
            , line [ x1 "10", y1 "10", x2 handX, y2 handY, stroke "#023963" ] []
            ]


toHexColor : Color -> String
toHexColor color =
    case color of
        Red ->
            "#a70d0d"

        Blue ->
            "#0099f6"

        Green ->
            "#00b844"

        Yellow ->
            "#ffc107"

        White ->
            "#fefefe"


padding =
    5


addPadding =
    (+) padding


noteBanks model =
    let
        toBank i noteBank =
            List.indexedMap
                (\j ac ->
                    rect
                        ([ fill <| toHexColor noteBank.color
                         , rx "2"
                         , ry "2"
                         , width "9"
                         , height "6"
                         , x << toString << addPadding << (*) 11 <| i
                         , y << toString << addPadding << (*) 8 <| j
                         , onClick <| Select i j
                         , stroke "chartreuse"
                         ]
                            ++ (hover [ ( "stroke-width", if (ac noteBank.notes) then "1px" else "0px" , "1px" ), ( "cursor", "normal", "pointer" ) ])
                        )
                        []
                )
                [.do, .re, .mi, .fa, .sol, .la, .ti, .do2]
                |> g []
    in
        List.indexedMap toBank model.noteBanks



-- UPDATE


type Msg
    = Tick
    | Select Int Int


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        Tick ->
            ( { model | step = (model.step + 1) % steps }, Cmd.none )

        Select i j ->
            ( model, Cmd.none )


init : ( Model, Cmd Msg )
init =
    ( { step = 0
      , noteBanks =
            [ Red, Green, Blue, Yellow, White ]
                |> List.map (\x -> { color = x, notes = initNotes })
      }
    , Cmd.none
    )


subs : Model -> Sub Msg
subs model =
    Time.every (250 * millisecond) (always Tick)
