module Main exposing (..)

import Array exposing (Array, get, set)
import DynamicStyle exposing (hover, hover_)
import Html exposing (Html, program, div)
import Html.Attributes exposing (attribute)
import Html.Events exposing (onClick)
import Svg exposing (circle, line, svg, g, rect, path)
import Svg.Attributes exposing (..)
import Time exposing (Time, second, millisecond)


main =
    program { init = init, view = view, update = update, subscriptions = subs }


type Color
    = Red
    | Blue
    | Green
    | Yellow
    | White


type alias Steps =
    Array (Array Color)


type alias Notes =
    Array Bool


type alias NoteBank =
    { color : Color
    , notes : Notes
    }



-- MODEL


type alias Model =
    { step : Int
    , noteBanks : Array NoteBank
    , steps : Array (Array Color)
    }



-- VIEW


numSteps : Int
numSteps =
    8


geometry =
    { circleSize = 30
    }


view : Model -> Html Msg
view model =
    svg [ viewBox "0 0 200 100", width "1600px", height "800px" ]
        [ rect [ x "0", y "0", width "200", height "100" ] []
        , g [ transform "translate(5, 5)", id "note-banks" ] (toSVGNoteBanks model)
        , g [ transform "translate(100, 10)" ]
            [ noteSequences model
              --, radialBars geometry.circleSize 50
              --, ticker model.step
            ]
        ]


ticker : Int -> Svg.Svg Msg
ticker step =
    let
        center =
            geometry.circleSize

        angle =
            turns <| toFloat step / toFloat numSteps

        handX =
            toString (center + (100) * cos (angle))

        handY =
            toString (center + (100) * sin (angle))
    in
        line [ x1 << toString <| geometry.circleSize, y1 << toString <| geometry.circleSize, x2 handX, y2 handY, stroke "black" ] []


joinNumbers =
    List.foldr ((++) << (++) " " << toString) ""


noteSequences : Model -> Svg.Svg Msg
noteSequences model =
    (g []) << Array.toList << (Array.indexedMap (noteSequence model.steps)) <| model.noteBanks


noteSequence : Steps -> Int -> NoteBank -> Svg.Svg Msg
noteSequence stepState level noteBank =
    let
        noteArc color level beat =
            let
                center =
                    geometry.circleSize

                angle =
                    360 / (toFloat numSteps)

                startAngle =
                    (angle * (toFloat beat))

                endAngle =
                    (angle * (toFloat (beat + 1)))

                arcPadding =
                    0

                radius =
                    (toFloat level) * (arcStrokeWidth + 1)

                angleInRadians deg =
                    (deg - 90) * pi / 180

                polarToCartesian radius angleInDegrees =
                    { x = center + (radius * cos (angleInRadians angleInDegrees))
                    , y = center + (radius * sin (angleInRadians angleInDegrees))
                    }

                isActive =
                    hasNote beat color stepState

                describeArc radius startAngle endAngle =
                    let
                        start =
                            polarToCartesian radius (endAngle - arcPadding)

                        end =
                            polarToCartesian radius (startAngle + arcPadding)

                        largeArcFlag =
                            if endAngle - startAngle <= 180 then
                                0
                            else
                                1

                        m =
                            [ .x start, .y start ] |> joinNumbers

                        a =
                            [ radius, radius, 0, largeArcFlag, 0, end.x, end.y ] |> joinNumbers
                    in
                        "M" ++ m ++ "A" ++ a |> Svg.Attributes.d
            in
                g []
                    [ Svg.path
                        [ describeArc radius startAngle (endAngle + 0.2)
                        , stroke <| toHexColor color
                        , strokeWidth <| toString arcStrokeWidth
                        , onClick <| SelectBeat color beat
                        ]
                        []
                    , Svg.path
                        [ describeArc radius (startAngle + 0.5) (endAngle - 0.5)
                        , stroke <|
                            if isActive then
                                toHexColor color
                            else
                                "black"
                        , strokeWidth <| toString (arcStrokeWidth - 0.5)
                        , onClick <| SelectBeat color beat
                        ]
                        []
                    ]
    in
        List.range 0 (numSteps - 1)
            |> List.map
                (\i ->
                    (noteArc noteBank.color (level + 1) i)
                )
            |> g []


arcStrokeWidth =
    6


radialBars : Float -> Float -> Svg.Svg Msg
radialBars center length =
    let
        toBar i =
            let
                angle =
                    turns <| toFloat i / toFloat numSteps

                handX =
                    toString (center + length * cos (angle))

                handY =
                    toString (center + length * sin (angle))
            in
                line [ x1 << toString <| center, y1 << toString <| center, x2 handX, y2 handY, stroke "black" ] []
    in
        List.range 0 numSteps |> List.map toBar |> g []


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


toSVGNoteBanks model =
    let
        hPadding =
            4

        vPadding =
            2

        w =
            10 - sw

        h =
            6 - sw

        sw =
            0.4

        noteBox color i j note =
            rect
                ([ fill <| toHexColor color
                 , fillOpacity <|
                    if note then
                        "1"
                    else
                        "0"
                 , rx "2"
                 , ry "2"
                 , width << toString <| w
                 , height << toString <| h
                 , x << toString << (*) (w + hPadding) <| toFloat <| i
                 , y << toString << (*) (h + vPadding) <| toFloat <| j
                 , onClick <| Select i j
                 , stroke <| toHexColor color
                 , strokeWidth << toString <| sw
                 ]
                    ++ (hover
                            [ ( "cursor", "normal", "pointer" )
                            ]
                       )
                )
                []

        bank i noteBank =
            noteBank.notes
                |> Array.indexedMap (noteBox noteBank.color i)
                |> Array.toList
                |> g []
    in
        Array.indexedMap bank model.noteBanks |> Array.toList



-- UPDATE


type Msg
    = Tick
    | Select Int Int
    | SelectBeat Color Int


setNoteBanks : Array NoteBank -> Model -> Model
setNoteBanks newBanks model =
    { model | noteBanks = newBanks }


setSteps : Array (Array Color) -> Model -> Model
setSteps newSteps model =
    { model | steps = newSteps }


hasNote : Int -> Color -> Steps -> Bool
hasNote stepIndex color =
    not
        << Array.isEmpty
        << Array.filter ((==) color)
        << Maybe.withDefault Array.empty
        << Array.get stepIndex


updateStep : Int -> Color -> Array (Array Color) -> Array (Array Color)
updateStep stepIndex color steps =
    let
        removeNote =
            Array.filter ((/=) color) theBeat

        addNote =
            Array.push color theBeat

        theBeat =
            Array.get stepIndex steps |> Maybe.withDefault Array.empty

        update x =
            Array.set stepIndex x steps
    in
        if hasNote stepIndex color steps then
            update removeNote
        else
            update addNote


setNote : Int -> NoteBank -> NoteBank
setNote index bank =
    let
        oldNote =
            Array.get index bank.notes |> Maybe.withDefault False

        newNote =
            not oldNote
    in
        { bank | notes = Array.set index newNote bank.notes }


asNoteBanksIn : Model -> Array NoteBank -> Model
asNoteBanksIn =
    flip setNoteBanks


asStepsIn : Model -> Array (Array Color) -> Model
asStepsIn =
    flip setSteps


updateNoteBanks : Int -> Int -> Array NoteBank -> Array NoteBank
updateNoteBanks bankIndex noteIndex =
    Array.indexedMap
        (\index bank ->
            if index == bankIndex then
                setNote noteIndex bank
            else
                bank
        )


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        Tick ->
            ( { model | step = (model.step + 1) % numSteps }, Cmd.none )

        Select i j ->
            let
                newModel =
                    model.noteBanks
                        |> updateNoteBanks i j
                        |> asNoteBanksIn model
            in
                newModel ! []

        SelectBeat color beat ->
            let
                newModel =
                    model.steps
                        |> updateStep beat color
                        |> asStepsIn model
            in
                newModel ! []


noteCount : Int
noteCount =
    9


initNotes : Notes
initNotes =
    Array.repeat noteCount False


initSteps =
    Array.repeat numSteps (Array.empty)


init : ( Model, Cmd Msg )
init =
    ( { step = 0
      , steps = initSteps
      , noteBanks =
            [ Red, Green, Blue, Yellow, White ]
                |> Array.fromList
                |> Array.map (\x -> { color = x, notes = initNotes })
      }
    , Cmd.none
    )


subs : Model -> Sub Msg
subs model =
    Time.every (250 * millisecond) (always Tick)
